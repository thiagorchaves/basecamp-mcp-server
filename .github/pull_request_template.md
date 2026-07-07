## Summary

Describe the change and why it is needed.

## Validation

- [ ] `uv run ruff format --check .`
- [ ] `uv run ruff check .`
- [ ] `uv run mypy basecamp_mcp`
- [ ] `uv run pytest`
- [ ] No real Basecamp credentials, IDs, emails, or API responses were added.
- [ ] New write operations are gated by `BASECAMP_ENABLE_WRITE_TOOLS`.
