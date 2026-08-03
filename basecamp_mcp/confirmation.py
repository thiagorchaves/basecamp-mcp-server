from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import threading
import time
from dataclasses import dataclass
from typing import Any

from .config import env_int
from .errors import BasecampError


@dataclass(frozen=True)
class PendingConfirmation:
    action: str
    fingerprint: str
    expires_at: float


_CONFIRMATIONS: dict[str, PendingConfirmation] = {}
_LOCK = threading.Lock()
_MAX_PENDING = 500


def _ttl_seconds() -> int:
    return env_int("BASECAMP_CONFIRMATION_TTL_SECONDS", 300, minimum=30)


def _fingerprint(payload: dict[str, Any]) -> str:
    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def _purge_expired(now: float) -> None:
    expired = [token for token, item in _CONFIRMATIONS.items() if item.expires_at <= now]
    for token in expired:
        _CONFIRMATIONS.pop(token, None)


def issue_confirmation(action: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Issue a short-lived, single-use token bound to an exact preview payload."""
    now = time.time()
    ttl = _ttl_seconds()
    token = secrets.token_urlsafe(32)
    pending = PendingConfirmation(
        action=action,
        fingerprint=_fingerprint(payload),
        expires_at=now + ttl,
    )

    with _LOCK:
        _purge_expired(now)
        if len(_CONFIRMATIONS) >= _MAX_PENDING:
            oldest = min(_CONFIRMATIONS, key=lambda key: _CONFIRMATIONS[key].expires_at)
            _CONFIRMATIONS.pop(oldest, None)
        _CONFIRMATIONS[token] = pending

    return {
        "confirmation_id": token,
        "confirmation_expires_in_seconds": ttl,
        "confirmation_single_use": True,
    }


def consume_confirmation(action: str, payload: dict[str, Any], confirmation_id: str) -> None:
    """Consume a preview token and verify that the write matches the preview exactly."""
    if not confirmation_id:
        raise BasecampError(
            "confirmation_id is required. Generate a preview, show it to the user, "
            "and pass the returned confirmation_id only after explicit approval."
        )

    now = time.time()
    with _LOCK:
        _purge_expired(now)
        pending = _CONFIRMATIONS.pop(confirmation_id, None)

    if pending is None:
        raise BasecampError("confirmation_id is invalid, expired, or has already been used.")
    if pending.action != action:
        raise BasecampError("confirmation_id was issued for a different action.")
    if not hmac.compare_digest(pending.fingerprint, _fingerprint(payload)):
        raise BasecampError(
            "The requested write no longer matches the approved preview. Generate a new preview."
        )
