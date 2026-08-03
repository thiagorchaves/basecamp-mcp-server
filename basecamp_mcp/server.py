from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

from mcp.server.fastmcp import FastMCP

from .config import BasecampConfig, env_bool, env_int
from .tools.card_tables import (
    find_cards_by_assignee,
    find_cards_by_title,
    get_card_table,
    get_my_cards,
    list_cards,
    list_project_card_tables,
)
from .tools.comments import add_comment, comment_recording_from_markdown, get_recording
from .tools.confirmed_cards import (
    add_card_update,
    add_investigation_report_to_card,
    preview_card_due_date,
    preview_card_update,
    preview_investigation_report_to_card,
    update_card_due_date,
)
from .tools.messages import (
    create_message,
    create_project_message,
    create_project_message_from_markdown,
    list_messages,
)
from .tools.projects import (
    find_project_by_name,
    find_projects,
    get_project,
    get_project_tools,
    list_projects,
)
from .tools.todos import (
    create_todo,
    create_todo_from_markdown,
    find_todos_by_title,
    list_project_todolists,
    list_project_todos,
    list_todolists,
    list_todos,
    update_card_by_title,
)

mcp = FastMCP("basecamp-mcp")


def writes_enabled() -> bool:
    return env_bool("BASECAMP_ENABLE_WRITE_TOOLS", default=False)


@mcp.tool()
def healthcheck() -> dict[str, Any]:
    """Validate that the MCP server is loaded and report non-secret configuration state."""
    return {
        "ok": True,
        "account_id_present": bool(os.getenv("BASECAMP_ACCOUNT_ID")),
        "access_token_present": bool(os.getenv("BASECAMP_ACCESS_TOKEN")),
        "user_agent_present": bool(os.getenv("BASECAMP_USER_AGENT")),
        "write_tools_enabled": writes_enabled(),
        "preview_bound_card_confirmations": True,
        "confirmation_ttl_seconds": env_int("BASECAMP_CONFIRMATION_TTL_SECONDS", 300, minimum=30),
        "api_base": os.getenv("BASECAMP_API_BASE", "https://3.basecampapi.com"),
    }


def _register(functions: list[Callable[..., Any]]) -> None:
    for function in functions:
        mcp.tool()(function)


_register(
    [
        list_projects,
        find_projects,
        find_project_by_name,
        get_project,
        get_project_tools,
        list_messages,
        list_todolists,
        list_project_todolists,
        list_todos,
        list_project_todos,
        find_todos_by_title,
        get_recording,
        list_project_card_tables,
        get_card_table,
        list_cards,
        find_cards_by_title,
        find_cards_by_assignee,
        get_my_cards,
        preview_card_update,
        preview_card_due_date,
        preview_investigation_report_to_card,
    ]
)

if writes_enabled():
    _register(
        [
            create_message,
            create_project_message,
            create_project_message_from_markdown,
            create_todo,
            create_todo_from_markdown,
            update_card_by_title,
            add_comment,
            comment_recording_from_markdown,
            add_card_update,
            update_card_due_date,
            add_investigation_report_to_card,
        ]
    )


def main() -> None:
    BasecampConfig.from_env()
    mcp.run()


if __name__ == "__main__":
    main()
