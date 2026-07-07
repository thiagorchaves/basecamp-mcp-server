from __future__ import annotations

from typing import Any

from ..base import client
from ..markdown import markdown_to_basecamp_html


def add_comment(recording_id: int, content_html: str) -> dict[str, Any]:
    """Adiciona comentário em qualquer recording do Basecamp, como mensagem, to-do ou documento."""
    return client().request(
        "POST", f"recordings/{recording_id}/comments.json", json={"content": content_html}
    )


def comment_recording_from_markdown(recording_id: int, markdown: str) -> dict[str, Any]:
    """Converte Markdown simples para HTML e comenta em qualquer recording do Basecamp."""
    return add_comment(recording_id, markdown_to_basecamp_html(markdown))


def get_recording(recording_id: int) -> dict[str, Any]:
    """Busca um recording genérico do Basecamp pelo ID."""
    return client().request("GET", f"recordings/{recording_id}.json")
