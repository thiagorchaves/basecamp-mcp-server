from __future__ import annotations

from datetime import date
from typing import Any

from ..confirmation import consume_confirmation, issue_confirmation
from ..errors import BasecampError
from ..markdown import markdown_to_basecamp_html
from . import card_tables
from .comments import comment_recording_from_markdown


def _resolved_card(project_name: str, card_title: str) -> dict[str, Any]:
    resolved = card_tables._resolve_single_card(project_name, card_title)
    if not resolved.get("ok"):
        return resolved
    return {"ok": True, "card": resolved["card"]}


def _card_identity(card: dict[str, Any]) -> dict[str, Any]:
    return {
        "card_id": card.get("id"),
        "card_title": card.get("title") or card.get("content"),
        "card_url": card.get("app_url"),
        "column": card.get("column_title"),
        "card_table": card.get("_card_table_title"),
    }


def preview_card_update(project_name: str, card_title: str, update_markdown: str) -> dict[str, Any]:
    """Preview a card comment and issue a short-lived confirmation token for that exact write."""
    resolved = _resolved_card(project_name, card_title)
    if not resolved.get("ok"):
        return resolved

    card = resolved["card"]
    payload = {
        "project_name": project_name,
        "card_id": int(card["id"]),
        "update_markdown": update_markdown,
    }
    confirmation = issue_confirmation("add_card_update", payload)
    return {
        "ok": True,
        "action": "preview_only",
        **_card_identity(card),
        "comment_html_preview": markdown_to_basecamp_html(update_markdown),
        "requires_explicit_confirmation": True,
        **confirmation,
    }


def add_card_update(
    project_name: str,
    card_title: str,
    update_markdown: str,
    confirmation_id: str,
) -> dict[str, Any]:
    """Publish a card comment only when it exactly matches a valid preview token."""
    resolved = _resolved_card(project_name, card_title)
    if not resolved.get("ok"):
        return resolved

    card = resolved["card"]
    payload = {
        "project_name": project_name,
        "card_id": int(card["id"]),
        "update_markdown": update_markdown,
    }
    consume_confirmation("add_card_update", payload, confirmation_id)
    comment = comment_recording_from_markdown(int(card["id"]), update_markdown)
    return {
        "ok": True,
        **_card_identity(card),
        "comment": comment,
        "confirmation_consumed": True,
    }


def preview_card_due_date(project_name: str, card_title: str, due_on: str) -> dict[str, Any]:
    """Preview a due-date change and issue a token bound to the target card and date."""
    try:
        date.fromisoformat(due_on)
    except ValueError as exc:
        raise BasecampError(
            f"due_on must use YYYY-MM-DD and be a valid calendar date, received: '{due_on}'"
        ) from exc

    resolved = _resolved_card(project_name, card_title)
    if not resolved.get("ok"):
        return resolved

    card = resolved["card"]
    payload = {"card_id": int(card["id"]), "due_on": due_on}
    confirmation = issue_confirmation("update_card_due_date", payload)
    return {
        "ok": True,
        "action": "preview_only",
        **_card_identity(card),
        "current_due_on": card.get("due_on"),
        "new_due_on": due_on,
        "requires_explicit_confirmation": True,
        **confirmation,
    }


def update_card_due_date(card_id: int, due_on: str, confirmation_id: str) -> dict[str, Any]:
    """Change a card due date only when it matches a valid preview token."""
    payload = {"card_id": card_id, "due_on": due_on}
    consume_confirmation("update_card_due_date", payload, confirmation_id)
    result = card_tables.update_card_due_date(card_id, due_on)
    result["confirmation_consumed"] = True
    return result


def _formatted_investigation_report(report_markdown: str) -> str:
    return (
        f"📋 **Relatório de Investigação**\n\n{report_markdown}\n\n---\n_Gerado via MCP Basecamp_"
    )


def preview_investigation_report_to_card(
    project_name: str,
    card_title: str,
    report_markdown: str,
) -> dict[str, Any]:
    """Preview an investigation report and issue a token for the exact report and card."""
    resolved = _resolved_card(project_name, card_title)
    if not resolved.get("ok"):
        return resolved

    card = resolved["card"]
    payload = {
        "project_name": project_name,
        "card_id": int(card["id"]),
        "report_markdown": report_markdown,
    }
    confirmation = issue_confirmation("add_investigation_report_to_card", payload)
    formatted = _formatted_investigation_report(report_markdown)
    return {
        "ok": True,
        "action": "preview_only",
        **_card_identity(card),
        "report_html_preview": markdown_to_basecamp_html(formatted),
        "requires_explicit_confirmation": True,
        **confirmation,
    }


def add_investigation_report_to_card(
    project_name: str,
    card_title: str,
    report_markdown: str,
    confirmation_id: str,
) -> dict[str, Any]:
    """Publish an investigation report only when it matches a valid preview token."""
    resolved = _resolved_card(project_name, card_title)
    if not resolved.get("ok"):
        return resolved

    card = resolved["card"]
    payload = {
        "project_name": project_name,
        "card_id": int(card["id"]),
        "report_markdown": report_markdown,
    }
    consume_confirmation("add_investigation_report_to_card", payload, confirmation_id)
    comment = comment_recording_from_markdown(
        int(card["id"]), _formatted_investigation_report(report_markdown)
    )
    return {
        "ok": True,
        **_card_identity(card),
        "report_type": "investigation",
        "comment": comment,
        "confirmation_consumed": True,
    }
