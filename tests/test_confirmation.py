import pytest

from basecamp_mcp import confirmation
from basecamp_mcp.errors import BasecampError


def test_confirmation_is_single_use(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BASECAMP_CONFIRMATION_TTL_SECONDS", "300")
    payload = {"card_id": 10, "due_on": "2026-08-10"}
    issued = confirmation.issue_confirmation("update_card_due_date", payload)

    confirmation.consume_confirmation("update_card_due_date", payload, issued["confirmation_id"])

    with pytest.raises(BasecampError, match="invalid, expired, or has already been used"):
        confirmation.consume_confirmation(
            "update_card_due_date", payload, issued["confirmation_id"]
        )


def test_confirmation_is_bound_to_exact_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BASECAMP_CONFIRMATION_TTL_SECONDS", "300")
    issued = confirmation.issue_confirmation(
        "add_card_update",
        {"project_name": "Ops", "card_id": 10, "update_markdown": "approved"},
    )

    with pytest.raises(BasecampError, match="no longer matches"):
        confirmation.consume_confirmation(
            "add_card_update",
            {"project_name": "Ops", "card_id": 10, "update_markdown": "changed"},
            issued["confirmation_id"],
        )


def test_missing_confirmation_is_rejected() -> None:
    with pytest.raises(BasecampError, match="confirmation_id is required"):
        confirmation.consume_confirmation("action", {"value": 1}, "")
