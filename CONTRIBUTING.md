# Contributing

Thank you for helping improve Basecamp MCP Server.

## Development setup

```bash
git clone https://github.com/thiagorchaves/basecamp-mcp-server.git
cd basecamp-mcp-server
uv sync --extra dev
```

Run the checks before opening a pull request:

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy basecamp_mcp
uv run pytest
```

## Pull requests

- Keep changes focused and explain the user-facing behavior.
- Add tests for bug fixes and new tools.
- Never include real Basecamp responses, tokens, account IDs, emails, or project names.
- Preserve preview-before-write behavior for title-based mutations.
- New mutation tools must remain behind `BASECAMP_ENABLE_WRITE_TOOLS`.

## Commit style

Conventional Commits are welcome, for example:

```text
feat: add card movement tool
fix: follow pagination for message boards
docs: clarify Kiro setup
```
