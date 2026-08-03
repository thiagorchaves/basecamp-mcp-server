import pytest

from basecamp_mcp.errors import BasecampError
from basecamp_mcp.tools import confirmed_cards


def _card() -> dict[str, object]:
    return {
        "id": 10,
        "title": "Investigate latency",
        "app_url": "https://example.invalid/card/10",
        "column_title": "Doing",
        "_card_table_title": "Operations",
        "due_on": "2026-08-01",
    }


def test_preview_then_write_consumes_exact_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BASECAMP_CONFIRMATION_TTL_SECONDS", "300")
    monkeypatch.setattr(
        confirmed_cards.card_tables,
        "_resolve_single_card",
        lambda project_name, card_title: {"ok": True, "card": _card()},
    )
    monkeypatch.setattr(
        confirmed_cards,
        "comment_recording_from_markdown",
        lambda card_id, markdown: {"id": 99, "content": markdown},
    )

    preview = confirmed_cards.preview_card_update("Ops", "Investigate latency", "**Done**")
    result = confirmed_cards.add_card_update(
        "Ops",
        "Investigate latency",
        "**Done**",
        preview["confirmation_id"],
    )

    assert preview["action"] == "preview_only"
    assert preview["requires_explicit_confirmation"] is True
    assert result["confirmation_consumed"] is True
    assert result["card_id"] == 10


def test_changed_payload_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BASECAMP_CONFIRMATION_TTL_SECONDS", "300")
    monkeypatch.setattr(
        confirmed_cards.card_tables,
        "_resolve_single_card",
        lambda project_name, card_title: {"ok": True, "card": _card()},
    )

    preview = confirmed_cards.preview_card_update("Ops", "Investigate latency", "approved")

    with pytest.raises(BasecampError, match="no longer matches"):
        confirmed_cards.add_card_update(
            "Ops",
            "Investigate latency",
            "different text",
            preview["confirmation_id"],
        )


def test_due_date_requires_preview_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BASECAMP_CONFIRMATION_TTL_SECONDS", "300")
    monkeypatch.setattr(
        confirmed_cards.card_tables,
        "_resolve_single_card",
        lambda project_name, card_title: {"ok": True, "card": _card()},
    )
    monkeypatch.setattr(
        confirmed_cards.card_tables,
        "update_card_due_date",
        lambda card_id, due_on: {"ok": True, "card_id": card_id, "due_on": due_on},
    )

    preview = confirmed_cards.preview_card_due_date("Ops", "Investigate latency", "2026-08-20")
    result = confirmed_cards.update_card_due_date(10, "2026-08-20", preview["confirmation_id"])

    assert result["confirmation_consumed"] is True


def test_invalid_due_date_is_rejected_before_token_issue(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(BasecampError, match="valid calendar date"):
        confirmed_cards.preview_card_due_date("Ops", "Investigate latency", "2026-02-31")
