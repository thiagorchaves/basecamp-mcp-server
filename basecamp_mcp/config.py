from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from .errors import BasecampError

load_dotenv()


def env(name: str, required: bool = True, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if required and not value:
        raise BasecampError(f"Missing required env var: {name}")
    return value or ""


def env_int(name: str, default: int, minimum: int = 0) -> int:
    raw = env(name, required=False, default=str(default))
    try:
        value = int(raw)
    except ValueError as exc:
        raise BasecampError(f"Environment variable {name} must be an integer") from exc
    if value < minimum:
        raise BasecampError(f"Environment variable {name} must be >= {minimum}")
    return value


def env_bool(name: str, default: bool = False) -> bool:
    raw = env(name, required=False, default=str(default)).strip().lower()
    if raw in {"1", "true", "yes", "on"}:
        return True
    if raw in {"0", "false", "no", "off"}:
        return False
    raise BasecampError(f"Environment variable {name} must be a boolean")


@dataclass(frozen=True)
class BasecampConfig:
    account_id: str
    access_token: str
    user_agent: str
    api_base: str = "https://3.basecampapi.com"
    timeout_seconds: int = 30
    max_pages: int = 100
    max_retries: int = 2

    @classmethod
    def from_env(cls) -> BasecampConfig:
        return cls(
            account_id=env("BASECAMP_ACCOUNT_ID"),
            access_token=env("BASECAMP_ACCESS_TOKEN"),
            user_agent=env("BASECAMP_USER_AGENT"),
            api_base=env(
                "BASECAMP_API_BASE",
                required=False,
                default="https://3.basecampapi.com",
            ),
            timeout_seconds=env_int("BASECAMP_TIMEOUT_SECONDS", 30, minimum=1),
            max_pages=env_int("BASECAMP_MAX_PAGES", 100, minimum=1),
            max_retries=env_int("BASECAMP_MAX_RETRIES", 2, minimum=0),
        )
