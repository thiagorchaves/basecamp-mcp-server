from __future__ import annotations

from typing import Any

from ..base import client, compact_project, normalize
from ..errors import BasecampError


def list_projects(status: str = "active") -> list[dict[str, Any]]:
    """Lista projetos do Basecamp. status pode ser active, archived ou trashed."""
    if status not in {"active", "archived", "trashed"}:
        raise BasecampError("status deve ser active, archived ou trashed")
    path = "projects.json" if status == "active" else f"projects.json?status={status}"
    projects = client().request_all(path)
    return [compact_project(project) for project in projects]


def find_projects(query: str, status: str = "active") -> list[dict[str, Any]]:
    """Busca projetos pelo nome ou descrição."""
    q = normalize(query)
    projects = list_projects(status=status)
    return [
        p
        for p in projects
        if q in normalize(p.get("name", "")) or q in normalize(p.get("description", ""))
    ]


def find_project_by_name(name: str) -> dict[str, Any]:
    """Encontra um único projeto por nome. Retorna opções se houver ambiguidade."""
    matches = find_projects(name)
    exact = [p for p in matches if normalize(p.get("name", "")) == normalize(name)]
    if len(exact) == 1:
        return exact[0]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise BasecampError(f"Nenhum projeto encontrado para: {name}")
    raise BasecampError(f"Mais de um projeto encontrado para '{name}': {matches}")


def get_project(project_id: int) -> dict[str, Any]:
    """Obtém detalhes de um projeto, incluindo dock com message_board, todoset, vault etc."""
    return client().request("GET", f"projects/{project_id}.json")


def get_project_tools(project_id: int) -> dict[str, Any]:
    """Lista os IDs das ferramentas do projeto, como message_board, todoset e vault."""
    project = get_project(project_id)
    tools: dict[str, Any] = {}
    for item in project.get("dock", []):
        tools[item.get("name", "unknown")] = {
            "id": item.get("id"),
            "title": item.get("title"),
            "url": item.get("url"),
            "app_url": item.get("app_url"),
            "enabled": item.get("enabled"),
        }
    return tools
