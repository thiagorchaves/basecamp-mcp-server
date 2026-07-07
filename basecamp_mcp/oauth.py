from __future__ import annotations

import argparse
import os
import secrets
import webbrowser
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse

import httpx
from dotenv import load_dotenv, set_key

AUTH_URL = "https://launchpad.37signals.com/authorization/new"
TOKEN_URL = "https://launchpad.37signals.com/authorization/token"  # noqa: S105
AUTHORIZATION_URL = "https://launchpad.37signals.com/authorization.json"


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise SystemExit(f"Missing {name} in the environment or .env file")
    return value


def _save_token_data(env_file: Path, token_data: dict[str, Any], user_agent: str) -> None:
    access_token = str(token_data["access_token"])
    set_key(str(env_file), "BASECAMP_ACCESS_TOKEN", access_token)

    refresh_token = token_data.get("refresh_token")
    if refresh_token:
        set_key(str(env_file), "BASECAMP_REFRESH_TOKEN", str(refresh_token))

    expires_in = token_data.get("expires_in")
    if isinstance(expires_in, int):
        expires_at = datetime.now(UTC) + timedelta(seconds=expires_in)
        set_key(str(env_file), "BASECAMP_ACCESS_TOKEN_EXPIRES_AT", expires_at.isoformat())

    with httpx.Client(timeout=30, headers={"User-Agent": user_agent}) as client:
        response = client.get(
            AUTHORIZATION_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        accounts = [
            account
            for account in response.json().get("accounts", [])
            if account.get("product") == "bc3"
        ]

    configured_account = os.getenv("BASECAMP_ACCOUNT_ID")
    if not configured_account and len(accounts) == 1:
        set_key(str(env_file), "BASECAMP_ACCOUNT_ID", str(accounts[0]["id"]))
        print(f"Basecamp account selected automatically: {accounts[0]['name']}")
    elif not configured_account and len(accounts) > 1:
        print("Multiple Basecamp accounts are available. Set BASECAMP_ACCOUNT_ID to one of:")
        for account in accounts:
            print(f"- {account['id']}: {account['name']}")


def _exchange_token(payload: dict[str, str]) -> dict[str, Any]:
    response = httpx.post(
        TOKEN_URL,
        data=payload,
        headers={"Accept": "application/json"},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    if "access_token" not in data:
        raise SystemExit("The OAuth response did not contain an access_token")
    return data


def _refresh(env_file: Path) -> None:
    client_id = _required("BASECAMP_CLIENT_ID")
    client_secret = _required("BASECAMP_CLIENT_SECRET")
    refresh_token = _required("BASECAMP_REFRESH_TOKEN")
    user_agent = _required("BASECAMP_USER_AGENT")

    token_data = _exchange_token(
        {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        }
    )
    _save_token_data(env_file, token_data, user_agent)
    print(f"Access token refreshed and saved to {env_file}")


def _authorize(env_file: Path) -> None:
    client_id = _required("BASECAMP_CLIENT_ID")
    client_secret = _required("BASECAMP_CLIENT_SECRET")
    redirect_uri = os.getenv("BASECAMP_REDIRECT_URI", "http://localhost:8000/callback")
    user_agent = _required("BASECAMP_USER_AGENT")

    redirect = urlparse(redirect_uri)
    if redirect.scheme != "http" or redirect.hostname not in {"localhost", "127.0.0.1"}:
        raise SystemExit("basecamp-oauth requires an http://localhost redirect URI")
    port = redirect.port or 80
    callback_path = redirect.path or "/callback"
    state = secrets.token_urlsafe(32)

    class OAuthHandler(BaseHTTPRequestHandler):
        completed = False

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            query = parse_qs(parsed.query)

            if parsed.path != callback_path:
                self.send_error(404)
                return
            if query.get("state", [None])[0] != state:
                self.send_error(400, "Invalid OAuth state")
                return
            if "error" in query:
                self.send_error(400, query.get("error_description", query["error"])[0])
                return

            code = query.get("code", [None])[0]
            if not code:
                self.send_error(400, "Missing authorization code")
                return

            try:
                token_data = _exchange_token(
                    {
                        "grant_type": "authorization_code",
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "redirect_uri": redirect_uri,
                        "code": code,
                    }
                )
                _save_token_data(env_file, token_data, user_agent)
            except Exception as exc:  # pragma: no cover - shown to the local operator
                self.send_error(500, str(exc))
                return

            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Basecamp authorization saved. You can close this tab.")
            type(self).completed = True

        def log_message(self, format: str, *args: object) -> None:
            return

    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
    }
    url = f"{AUTH_URL}?{urlencode(params)}"

    print("Open this URL to authorize Basecamp:")
    print(url)
    webbrowser.open(url)

    server = HTTPServer((redirect.hostname or "localhost", port), OAuthHandler)
    server.timeout = 300
    server.handle_request()
    server.server_close()

    if not OAuthHandler.completed:
        raise SystemExit("OAuth callback was not completed")
    print(f"OAuth credentials saved to {env_file}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Authorize or refresh Basecamp OAuth credentials")
    parser.add_argument("--refresh", action="store_true", help="refresh the current access token")
    parser.add_argument(
        "--env-file",
        default=os.getenv("BASECAMP_ENV_FILE", ".env"),
        help="dotenv file to update (default: .env)",
    )
    args = parser.parse_args()

    env_file = Path(args.env_file).expanduser().resolve()
    load_dotenv(env_file)
    env_file.touch(mode=0o600, exist_ok=True)
    env_file.chmod(0o600)

    if args.refresh:
        _refresh(env_file)
    else:
        _authorize(env_file)


if __name__ == "__main__":
    main()
