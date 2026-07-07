from __future__ import annotations

from typing import Any

from ..base import client, dock, normalize
from ..errors import BasecampError
from ..markdown import markdown_to_basecamp_html
from .comments import comment_recording_from_markdown
from .projects import find_project_by_name, get_project


def list_todolists(todoset_id: int, status: str = "active") -> list[dict[str, Any]]:
    """Lista to-do lists de um todoset."""
    status = status or "active"
    return client().request_all(f"todosets/{todoset_id}/todolists.json?status={status}")


def list_project_todolists(project_id: int, status: str = "active") -> list[dict[str, Any]]:
    """Lista to-do lists de um projeto, descobrindo o todoset_id automaticamente."""
    project = get_project(project_id)
    todoset = dock(project, "todoset")
    if not todoset or not todoset.get("id"):
        raise BasecampError("Projeto não possui todoset habilitado ou ID não encontrado.")
    return list_todolists(int(todoset["id"]), status=status)


def list_todos(todolist_id: int, status: str = "active") -> list[dict[str, Any]]:
    """Lista to-dos de uma to-do list."""
    status = status or "active"
    return client().request_all(f"todolists/{todolist_id}/todos.json?status={status}")


def list_project_todos(project_id: int, status: str = "active") -> list[dict[str, Any]]:
    """Lista todos os to-dos de todas as listas de um projeto."""
    items: list[dict[str, Any]] = []
    for todolist in list_project_todolists(project_id, status=status):
        for todo in list_todos(int(todolist["id"]), status=status):
            todo["todolist_id"] = todolist.get("id")
            todo["todolist_title"] = todolist.get("title") or todolist.get("name")
            items.append(todo)
    return items


def find_todos_by_title(
    project_name: str, title: str, status: str = "active"
) -> list[dict[str, Any]]:
    """Busca to-dos/cards pelo título dentro de um projeto."""
    project = find_project_by_name(project_name)
    q = normalize(title)
    todos = list_project_todos(int(project["id"]), status=status)
    return [
        todo for todo in todos if q in normalize(todo.get("content", "") or todo.get("title", ""))
    ]


def create_todo(todolist_id: int, content: str, description_html: str = "") -> dict[str, Any]:
    """Cria um to-do em uma lista."""
    payload = {"content": content}
    if description_html:
        payload["description"] = description_html
    return client().request("POST", f"todolists/{todolist_id}/todos.json", json=payload)


def create_todo_from_markdown(
    project_name: str, todolist_name: str, title: str, description_markdown: str = ""
) -> dict[str, Any]:
    """Cria um to-do procurando projeto e to-do list por nome."""
    project = find_project_by_name(project_name)
    lists = list_project_todolists(int(project["id"]))
    matches = [
        tl
        for tl in lists
        if normalize(todolist_name) in normalize(tl.get("title", "") or tl.get("name", ""))
    ]
    if len(matches) != 1:
        raise BasecampError(
            f"To-do list ambígua ou não encontrada para '{todolist_name}': {matches}"
        )
    html = markdown_to_basecamp_html(description_markdown) if description_markdown else ""
    return create_todo(int(matches[0]["id"]), title, html)


def update_card_by_title(
    project_name: str, card_title: str, comment_markdown: str
) -> dict[str, Any]:
    """Busca um card/to-do por título dentro de um projeto e adiciona comentário em Markdown.

    Se houver mais de um card parecido, não escreve e retorna as opções para o usuário decidir.
    """
    matches = find_todos_by_title(project_name, card_title)
    exact = [
        m
        for m in matches
        if normalize(m.get("content", "") or m.get("title", "")) == normalize(card_title)
    ]
    if len(exact) == 1:
        target = exact[0]
    elif len(matches) == 1:
        target = matches[0]
    elif not matches:
        raise BasecampError(
            f"Nenhum card parecido com '{card_title}' foi encontrado no projeto '{project_name}'."
        )
    else:
        return {
            "ok": False,
            "reason": "multiple_matches",
            "message": "Mais de um card encontrado. Nenhum comentário foi criado.",
            "matches": [
                {
                    "id": m.get("id"),
                    "content": m.get("content"),
                    "app_url": m.get("app_url"),
                    "todolist_title": m.get("todolist_title"),
                }
                for m in matches
            ],
        }

    comment = comment_recording_from_markdown(int(target["id"]), comment_markdown)
    return {
        "ok": True,
        "project_name": project_name,
        "card_id": target.get("id"),
        "card_title": target.get("content") or target.get("title"),
        "card_url": target.get("app_url"),
        "comment": comment,
    }
