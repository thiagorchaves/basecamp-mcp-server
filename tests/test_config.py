import pytest

from basecamp_mcp.config import BasecampConfig, env_bool
from basecamp_mcp.errors import BasecampError


def test_config_requires_identifying_user_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BASECAMP_ACCOUNT_ID", "123")
    monkeypatch.setenv("BASECAMP_ACCESS_TOKEN", "token")
    monkeypatch.delenv("BASECAMP_USER_AGENT", raising=False)

    with pytest.raises(BasecampError, match="BASECAMP_USER_AGENT"):
        BasecampConfig.from_env()


def test_env_bool(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FLAG", "yes")
    assert env_bool("FLAG") is True

    monkeypatch.setenv("FLAG", "banana")
    with pytest.raises(BasecampError, match="must be a boolean"):
        env_bool("FLAG")
