from __future__ import annotations

import time
from typing import Any

import httpx

from .config import BasecampConfig
from .errors import BasecampError

_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
_RETRYABLE_METHODS = {"GET", "HEAD"}


class BasecampClient:
    def __init__(
        self,
        config: BasecampConfig | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.config = config or BasecampConfig.from_env()
        self.transport = transport

    def url(self, path: str) -> str:
        if path.startswith(("https://", "http://")):
            return path
        base = self.config.api_base.rstrip("/")
        return f"{base}/{self.config.account_id}/{path.lstrip('/')}"

    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.config.access_token}",
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json",
            "User-Agent": self.config.user_agent,
        }

    def request(
        self,
        method: str,
        path: str,
        json: dict[str, Any] | None = None,
    ) -> Any:
        response = self._send(method, path, json=json)
        if response.status_code == 204 or not response.content:
            return {"ok": True}
        return response.json()

    def request_all(self, path: str) -> list[dict[str, Any]]:
        """Follow Basecamp Link headers and return every page in a collection."""
        items: list[dict[str, Any]] = []
        next_url: str | None = path
        pages = 0

        while next_url:
            pages += 1
            if pages > self.config.max_pages:
                raise BasecampError(
                    f"Pagination exceeded BASECAMP_MAX_PAGES={self.config.max_pages}"
                )

            response = self._send("GET", next_url)
            payload = response.json()
            if not isinstance(payload, list):
                raise BasecampError("Expected a JSON list from a Basecamp collection endpoint")
            items.extend(payload)

            next_link = response.links.get("next")
            next_url = next_link.get("url") if next_link else None

        return items

    def _send(
        self,
        method: str,
        path: str,
        json: dict[str, Any] | None = None,
    ) -> httpx.Response:
        method = method.upper()
        attempts = self.config.max_retries + 1 if method in _RETRYABLE_METHODS else 1

        with httpx.Client(
            timeout=self.config.timeout_seconds,
            headers=self.headers(),
            follow_redirects=True,
            transport=self.transport,
        ) as http:
            for attempt in range(attempts):
                try:
                    response = http.request(method, self.url(path), json=json)
                except httpx.RequestError as exc:
                    if attempt + 1 >= attempts:
                        raise BasecampError(f"Basecamp request failed: {exc}") from exc
                    time.sleep(2**attempt)
                    continue

                if response.status_code not in _RETRYABLE_STATUS_CODES:
                    break
                if attempt + 1 >= attempts:
                    break

                retry_after = response.headers.get("Retry-After")
                delay = int(retry_after) if retry_after and retry_after.isdigit() else 2**attempt
                time.sleep(min(delay, 30))

        if response.status_code >= 400:
            self._raise_api_error(response)
        return response

    def _raise_api_error(self, response: httpx.Response) -> None:
        body = response.text[:1000]
        status = response.status_code
        if status == 400:
            hint = "Bad request. Check the payload and BASECAMP_USER_AGENT."
        elif status == 401:
            hint = "Unauthorized. The access token may be expired or revoked."
        elif status == 403:
            hint = "Forbidden. The authenticated user may lack permission for this resource."
        elif status == 404:
            hint = "Not found. Check the account, resource ID, and resource visibility."
        elif status == 429:
            hint = "Rate limited. Retry later or reduce request frequency."
        else:
            hint = "Basecamp API returned an error."
        raise BasecampError(f"Basecamp API error {status}: {hint} Response: {body}")
