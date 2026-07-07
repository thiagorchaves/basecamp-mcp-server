from __future__ import annotations

from datetime import date
from typing import Any

from ..base import client, normalize
from ..errors import BasecampError
from ..markdown import markdown_to_basecamp_html
from .comments import comment_recording_from_markdown
from .projects import find_project_by_name, get_project

# ---------------------------------------------------------------------------
# Existing tools (maintained)
# ---------------------------------------------------------------------------


def list_project_card_tables(
    project_id: int, include_disabled: bool = False
) -> list[dict[str, Any]]:
    """Lista Card Tables (Kanban boards) de um projeto via dock.

    Retorna todas as card_tables encontradas no dock do projeto, incluindo
    ID, título, url e app_url.
    """
    project = get_project(project_id)
    tables: list[dict[str, Any]] = []
    for item in project.get("dock", []):
        if item.get("name") == "kanban_board" and (include_disabled or item.get("enabled")):
            tables.append(
                {
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "app_url": item.get("app_url"),
                    "enabled": item.get("enabled"),
                }
            )
    if not tables:
        raise BasecampError(f"Projeto {project_id} não possui Card Table (kanban_board) no dock.")
    return tables


def get_card_table(project_id: int, card_table_id: int) -> dict[str, Any]:
    """Retorna metadados e colunas de uma Card Table (Kanban board).

    Inclui as colunas (lists) com seus IDs, títulos e cards.
    """
    _ = project_id  # Kept for backwards-compatible MCP tool arguments.
    return client().request("GET", f"card_tables/{card_table_id}.json")


def _get_card_table_columns(project_id: int, card_table_id: int) -> list[dict[str, Any]]:
    """Retorna as colunas (lists) de uma Card Table."""
    table = get_card_table(project_id, card_table_id)
    lists = table.get("lists", [])
    return lists


def list_cards(project_id: int, card_table_id: int) -> list[dict[str, Any]]:
    """Lista todos os cards de todas as colunas de uma Card Table.

    Retorna cards com: id, title, content, app_url, assignees, coluna (column_title).
    """
    columns = _get_card_table_columns(project_id, card_table_id)
    all_cards: list[dict[str, Any]] = []

    for column in columns:
        column_title = column.get("title") or column.get("name", "")
        column_id = column.get("id")

        cards_url = f"card_tables/lists/{column_id}/cards.json"
        cards = client().request_all(cards_url)

        if not isinstance(cards, list):
            cards = []

        for card in cards:
            card["_column_title"] = column_title
            card["_column_id"] = column_id
            all_cards.append(_compact_card(card))

    return all_cards


def find_cards_by_title(project_name: str, title: str) -> list[dict[str, Any]]:
    """Busca cards por título aproximado dentro de Card Tables de um projeto.

    Procura em todas as Card Tables do projeto por cards cujo título contenha
    a string informada.
    """
    project = find_project_by_name(project_name)
    project_id = int(project["id"])
    tables = list_project_card_tables(project_id)

    q = normalize(title)
    results: list[dict[str, Any]] = []

    for table in tables:
        table_id = int(table["id"])
        cards = list_cards(project_id, table_id)
        for card in cards:
            card_title = card.get("title") or card.get("content") or ""
            if q in normalize(card_title):
                card["_card_table_title"] = table.get("title")
                results.append(card)

    return results


def find_cards_by_assignee(project_name: str, assignee_name_or_email: str) -> dict[str, Any]:
    """Busca cards por responsável (assignee) dentro de Card Tables de um projeto.

    Filtra cards que possuem o nome ou email informado entre seus assignees.
    Se a API do Basecamp não retornar assignees nos cards, informa a limitação.
    """
    project = find_project_by_name(project_name)
    project_id = int(project["id"])
    tables = list_project_card_tables(project_id)

    q = normalize(assignee_name_or_email)
    results: list[dict[str, Any]] = []
    has_assignee_data = False

    for table in tables:
        table_id = int(table["id"])
        cards = list_cards(project_id, table_id)
        for card in cards:
            assignees = card.get("assignees", [])
            if assignees:
                has_assignee_data = True
            for assignee in assignees:
                name = normalize(assignee.get("name", ""))
                email = normalize(assignee.get("email_address", ""))
                if q in name or q in email:
                    card["_card_table_title"] = table.get("title")
                    results.append(card)
                    break

    if not has_assignee_data and not results:
        return {
            "ok": False,
            "reason": "no_assignee_data",
            "message": (
                "A API do Basecamp não retornou dados de assignees nos cards. "
                "Isso pode ocorrer se os cards não possuem responsáveis atribuídos "
                "ou se o endpoint de listagem não inclui esse campo. "
                "Tente acessar cards individualmente ou verificar no Basecamp diretamente."
            ),
        }

    return {
        "ok": True,
        "assignee_query": assignee_name_or_email,
        "total_found": len(results),
        "cards": results,
    }


def comment_card(card_id: int, content_html: str) -> dict[str, Any]:
    """Adiciona comentário em um card do Kanban usando o endpoint genérico de recordings.

    Cards no Basecamp são recordings, então o endpoint de comments funciona normalmente.
    """
    return client().request(
        "POST", f"recordings/{card_id}/comments.json", json={"content": content_html}
    )


def update_card_table_card_by_title(
    project_name: str, card_title: str, comment_markdown: str
) -> dict[str, Any]:
    """Busca card no Card Table por título e adiciona comentário em Markdown.

    Se encontrar exatamente um card, comenta.
    Se encontrar vários, retorna as opções sem escrever.
    """
    matches = find_cards_by_title(project_name, card_title)
    exact = [
        m
        for m in matches
        if normalize(m.get("title") or m.get("content") or "") == normalize(card_title)
    ]

    if len(exact) == 1:
        target = exact[0]
    elif len(matches) == 1:
        target = matches[0]
    elif not matches:
        raise BasecampError(
            f"Nenhum card encontrado com título parecido com '{card_title}' "
            f"nas Card Tables do projeto '{project_name}'."
        )
    else:
        return {
            "ok": False,
            "reason": "multiple_matches",
            "message": "Mais de um card encontrado nas Card Tables. Nenhum comentário foi criado.",
            "matches": [
                {
                    "id": m.get("id"),
                    "title": m.get("title") or m.get("content"),
                    "app_url": m.get("app_url"),
                    "column": m.get("column_title"),
                    "card_table": m.get("_card_table_title"),
                }
                for m in matches
            ],
        }

    comment = comment_recording_from_markdown(int(target["id"]), comment_markdown)
    return {
        "ok": True,
        "project_name": project_name,
        "card_id": target.get("id"),
        "card_title": target.get("title") or target.get("content"),
        "card_url": target.get("app_url"),
        "column": target.get("column_title"),
        "comment": comment,
    }


# ---------------------------------------------------------------------------
# New workflow tools
# ---------------------------------------------------------------------------


def get_my_cards(project_name: str, assignee_name_or_email: str) -> dict[str, Any]:
    """Retorna cards atribuídos a uma pessoa, com título, coluna, due date e URL.

    Versão compacta focada no fluxo de trabalho: mostra apenas informações
    de acompanhamento (status, prazo, link) sem conteúdo do card.
    """
    result = find_cards_by_assignee(project_name, assignee_name_or_email)
    if not result.get("ok"):
        return result

    cards = result.get("cards", [])
    compact: list[dict[str, Any]] = []
    for card in cards:
        compact.append(
            {
                "card_id": card.get("id"),
                "title": card.get("title") or card.get("content"),
                "column": card.get("column_title"),
                "due_on": card.get("due_on"),
                "app_url": card.get("app_url"),
                "card_table": card.get("_card_table_title"),
                "updated_at": card.get("updated_at"),
            }
        )

    return {
        "ok": True,
        "assignee": assignee_name_or_email,
        "total": len(compact),
        "cards": compact,
    }


def _resolve_single_card(project_name: str, card_title: str) -> dict[str, Any]:
    """Resolve um card por título. Retorna o card ou dict de erro com múltiplos matches."""
    matches = find_cards_by_title(project_name, card_title)
    exact = [
        m
        for m in matches
        if normalize(m.get("title") or m.get("content") or "") == normalize(card_title)
    ]

    if len(exact) == 1:
        return {"ok": True, "card": exact[0]}
    elif len(matches) == 1:
        return {"ok": True, "card": matches[0]}
    elif not matches:
        raise BasecampError(
            f"Nenhum card encontrado com título parecido com '{card_title}' "
            f"nas Card Tables do projeto '{project_name}'."
        )
    else:
        return {
            "ok": False,
            "reason": "multiple_matches",
            "message": "Mais de um card encontrado. Nenhuma ação realizada.",
            "matches": [
                {
                    "id": m.get("id"),
                    "title": m.get("title") or m.get("content"),
                    "app_url": m.get("app_url"),
                    "column": m.get("column_title"),
                    "card_table": m.get("_card_table_title"),
                }
                for m in matches
            ],
        }


def preview_card_update(project_name: str, card_title: str, update_markdown: str) -> dict[str, Any]:
    """Mostra preview de um comentário em card sem escrever nada.

    Busca o card por título, gera o HTML do comentário e retorna:
    - card encontrado (título, coluna, URL)
    - preview do HTML que seria publicado

    Nenhuma escrita é realizada. Use para confirmar antes de add_card_update.
    """
    resolved = _resolve_single_card(project_name, card_title)
    if not resolved.get("ok"):
        return resolved

    card = resolved["card"]
    html_preview = markdown_to_basecamp_html(update_markdown)

    return {
        "ok": True,
        "action": "preview_only",
        "card_id": card.get("id"),
        "card_title": card.get("title") or card.get("content"),
        "card_url": card.get("app_url"),
        "column": card.get("column_title"),
        "card_table": card.get("_card_table_title"),
        "comment_html_preview": html_preview,
    }


def add_card_update(project_name: str, card_title: str, update_markdown: str) -> dict[str, Any]:
    """Busca card por título e adiciona comentário em Markdown.

    Se encontrar exatamente um card, converte markdown para HTML e comenta.
    Se encontrar vários, retorna opções sem escrever.
    """
    resolved = _resolve_single_card(project_name, card_title)
    if not resolved.get("ok"):
        return resolved

    card = resolved["card"]
    comment = comment_recording_from_markdown(int(card["id"]), update_markdown)

    return {
        "ok": True,
        "card_id": card.get("id"),
        "card_title": card.get("title") or card.get("content"),
        "card_url": card.get("app_url"),
        "column": card.get("column_title"),
        "comment": comment,
    }


def update_card_due_date(card_id: int, due_on: str) -> dict[str, Any]:
    """Altera data de vencimento de um card existente.

    due_on no formato YYYY-MM-DD.
    Não altera título, descrição ou responsável.
    """
    try:
        date.fromisoformat(due_on)
    except ValueError as exc:
        raise BasecampError(
            f"due_on deve estar no formato YYYY-MM-DD, recebido: '{due_on}'"
        ) from exc

    result = client().request("PUT", f"card_tables/cards/{card_id}.json", json={"due_on": due_on})
    return {
        "ok": True,
        "card_id": card_id,
        "due_on": due_on,
        "response": result,
    }


def add_investigation_report_to_card(
    project_name: str, card_title: str, report_markdown: str
) -> dict[str, Any]:
    """Adiciona relatório de investigação formatado como comentário em um card.

    Igual a add_card_update, mas formata o markdown como relatório estruturado:
    título, resumo, evidências, conclusão e próximos passos.

    O report_markdown deve seguir a estrutura:
    # Título
    ## Resumo
    ## Evidências
    ## Conclusão
    ## Próximos passos

    Se encontrar vários cards, retorna opções sem escrever.
    """
    resolved = _resolve_single_card(project_name, card_title)
    if not resolved.get("ok"):
        return resolved

    card = resolved["card"]

    # Wrap report in investigation header/footer
    formatted = (
        f"📋 **Relatório de Investigação**\n\n{report_markdown}\n\n---\n_Gerado via MCP Basecamp_"
    )
    comment = comment_recording_from_markdown(int(card["id"]), formatted)

    return {
        "ok": True,
        "card_id": card.get("id"),
        "card_title": card.get("title") or card.get("content"),
        "card_url": card.get("app_url"),
        "column": card.get("column_title"),
        "report_type": "investigation",
        "comment": comment,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _compact_card(card: dict[str, Any]) -> dict[str, Any]:
    """Retorna representação compacta de um card."""
    return {
        "id": card.get("id"),
        "title": card.get("title") or card.get("content"),
        "content": card.get("content"),
        "app_url": card.get("app_url"),
        "status": card.get("status"),
        "assignees": card.get("assignees", []),
        "column_title": card.get("_column_title"),
        "column_id": card.get("_column_id"),
        "due_on": card.get("due_on"),
        "created_at": card.get("created_at"),
        "updated_at": card.get("updated_at"),
    }
