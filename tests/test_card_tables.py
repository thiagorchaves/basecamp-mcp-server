import pytest

from basecamp_mcp.errors import BasecampError
from basecamp_mcp.tools import card_tables


class FakeClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, str] | None]] = []

    def request(
        self,
        method: str,
        path: str,
        json: dict[str, str] | None = None,
    ) -> dict[str, object]:
        self.calls.append((method, path, json))
        return {"id": 99, "due_on": json["due_on"] if json else None}


def test_update_card_due_date_uses_card_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeClient()
    monkeypatch.setattr(card_tables, "client", lambda: fake)

    result = card_tables.update_card_due_date(99, "2026-07-10")

    assert fake.calls == [("PUT", "card_tables/cards/99.json", {"due_on": "2026-07-10"})]
    assert result["ok"] is True


def test_update_card_due_date_validates_calendar_date() -> None:
    with pytest.raises(BasecampError, match="YYYY-MM-DD"):
        card_tables.update_card_due_date(99, "2026-02-31")


def test_preview_does_not_write(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        card_tables,
        "_resolve_single_card",
        lambda project_name, card_title: {
            "ok": True,
            "card": {
                "id": 10,
                "title": "Investigate latency",
                "app_url": "https://example.invalid/card/10",
                "column_title": "Doing",
                "_card_table_title": "Operations",
            },
        },
    )

    result = card_tables.preview_card_update("Ops", "Investigate latency", "**Done**")

    assert result["action"] == "preview_only"
    assert result["comment_html_preview"] == "<p><strong>Done</strong></p>"
