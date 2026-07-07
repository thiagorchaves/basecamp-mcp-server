import httpx
import pytest

from basecamp_mcp.client import BasecampClient
from basecamp_mcp.config import BasecampConfig
from basecamp_mcp.errors import BasecampError


def config(**overrides: object) -> BasecampConfig:
    values: dict[str, object] = {
        "account_id": "123",
        "access_token": "secret-token",
        "user_agent": "Basecamp MCP Tests (tests@example.com)",
        "api_base": "https://3.basecampapi.com",
        "timeout_seconds": 5,
        "max_pages": 5,
        "max_retries": 0,
    }
    values.update(overrides)
    return BasecampConfig(**values)  # type: ignore[arg-type]


def test_request_all_follows_link_header() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer secret-token"
        if request.url.params.get("page") == "2":
            return httpx.Response(200, json=[{"id": 2}])
        return httpx.Response(
            200,
            json=[{"id": 1}],
            headers={"Link": '<https://3.basecampapi.com/123/projects.json?page=2>; rel="next"'},
        )

    client = BasecampClient(config(), transport=httpx.MockTransport(handler))

    assert client.request_all("projects.json") == [{"id": 1}, {"id": 2}]


def test_request_all_rejects_non_list_payload() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={"id": 1}))
    client = BasecampClient(config(), transport=transport)

    with pytest.raises(BasecampError, match="Expected a JSON list"):
        client.request_all("projects.json")


def test_api_errors_do_not_include_the_access_token() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(401, text="unauthorized", request=request)
    )
    client = BasecampClient(config(), transport=transport)

    with pytest.raises(BasecampError) as exc_info:
        client.request("GET", "projects.json")

    assert "secret-token" not in str(exc_info.value)
