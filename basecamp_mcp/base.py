from __future__ import annotations

from typing import Any

from .client import BasecampClient


def client() -> BasecampClient:
    return BasecampClient()


def compact_project(project: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": project.get("id"),
        "name": project.get("name"),
        "description": project.get("description"),
        "status": project.get("status"),
        "app_url": project.get("app_url"),
        "created_at": project.get("created_at"),
        "updated_at": project.get("updated_at"),
    }


def dock(project: dict[str, Any], tool_name: str) -> dict[str, Any] | None:
    for item in project.get("dock", []):
        if item.get("name") == tool_name:
            return item
    return None


def normalize(text: str) -> str:
    return " ".join(str(text or "").lower().split())
