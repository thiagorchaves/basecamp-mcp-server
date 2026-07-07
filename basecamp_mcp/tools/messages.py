from __future__ import annotations

from typing import Any

from ..base import client, dock
from ..errors import BasecampError
from ..markdown import markdown_to_basecamp_html
from .projects import find_project_by_name, get_project


def list_messages(message_board_id: int) -> list[dict[str, Any]]:
    """Lista mensagens de um message board pelo ID da ferramenta message_board."""
    return client().request_all(f"message_boards/{message_board_id}/messages.json")


def create_message(
    message_board_id: int, subject: str, content_html: str, publish: bool = True
) -> dict[str, Any]:
    """Cria uma mensagem usando HTML simples permitido pelo Basecamp."""
    payload = {
        "subject": subject,
        "content": content_html,
        "status": "active" if publish else "draft",
    }
    return client().request(
        "POST", f"message_boards/{message_board_id}/messages.json", json=payload
    )


def create_project_message(
    project_id: int, subject: str, content_html: str, publish: bool = True
) -> dict[str, Any]:
    """Cria uma mensagem, descobrindo automaticamente o message_board_id."""
    project = get_project(project_id)
    board = dock(project, "message_board")
    if not board or not board.get("id"):
        raise BasecampError("Projeto não possui message_board habilitado ou ID não encontrado.")
    return create_message(int(board["id"]), subject, content_html, publish)


def create_project_message_from_markdown(
    project_name: str, subject: str, markdown: str, publish: bool = True
) -> dict[str, Any]:
    """Cria uma mensagem por projeto e converte Markdown simples para HTML."""
    project = find_project_by_name(project_name)
    content_html = markdown_to_basecamp_html(markdown)
    return create_project_message(int(project["id"]), subject, content_html, publish)
