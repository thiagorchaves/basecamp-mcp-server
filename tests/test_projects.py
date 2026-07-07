import pytest

from basecamp_mcp.errors import BasecampError
from basecamp_mcp.tools import projects


class FakeClient:
    def __init__(self) -> None:
        self.paths: list[str] = []

    def request_all(self, path: str) -> list[dict[str, object]]:
        self.paths.append(path)
        return [{"id": 1, "name": "Example", "status": "archived"}]


def test_archived_projects_use_status_query(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeClient()
    monkeypatch.setattr(projects, "client", lambda: fake)

    result = projects.list_projects("archived")

    assert fake.paths == ["projects.json?status=archived"]
    assert result[0]["name"] == "Example"


def test_invalid_project_status_is_rejected() -> None:
    with pytest.raises(BasecampError, match="active, archived ou trashed"):
        projects.list_projects("deleted")
