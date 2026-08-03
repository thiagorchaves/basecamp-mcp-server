# Basecamp MCP Server

[Português (Brasil)](README.pt-BR.md)

An open-source Model Context Protocol server for Basecamp projects, messages, to-dos, recordings, and Card Tables. It is designed for operational workflows where an AI assistant needs to retrieve context, prepare changes, and keep sensitive card mutations behind explicit, preview-bound approval.

> [!IMPORTANT]
> This is an independent community project. It is not affiliated with, sponsored by, or endorsed by 37signals or Basecamp.

![Basecamp MCP Server architecture](docs/basecamp-mcp-architecture.svg)

## Highlights

- Discover projects and enabled project tools.
- Search to-dos and Card Table cards by title or assignee.
- Follow Basecamp pagination automatically.
- Keep mutation tools disabled by default.
- Preview sensitive card updates before writing.
- Bind card comments, due-date changes, and investigation reports to short-lived, single-use confirmation tokens.
- Refuse ambiguous title-based writes when multiple items match.
- Support OAuth authorization and token refresh.
- Run linting, typing, tests, and dependency auditing in CI.

## How preview-bound confirmation works

Sensitive Card Table workflows use a two-step protocol:

1. Call a preview tool.
2. Show the preview to the user.
3. The preview returns a short-lived `confirmation_id` bound to the exact card and payload.
4. After explicit approval, call the matching write tool with that `confirmation_id`.
5. The server verifies that the requested write exactly matches the approved preview and consumes the token.

A confirmation token cannot be reused and cannot authorize a changed payload.

> [!NOTE]
> The server enforces preview-before-write and exact payload binding. The MCP host is responsible for forwarding the `confirmation_id` only after the user has actually approved the preview.

## Requirements

- Python 3.11 or newer.
- A Basecamp OAuth application or valid access token.
- An MCP-compatible stdio client such as Kiro, Claude Desktop, or another MCP host.

## Install from GitHub

```bash
uv tool install git+https://github.com/thiagorchaves/basecamp-mcp-server.git
```

For development:

```bash
git clone https://github.com/thiagorchaves/basecamp-mcp-server.git
cd basecamp-mcp-server
uv sync --extra dev
```

## Configure Basecamp OAuth

Register an application in the 37signals integrations console and use this redirect URI:

```text
http://localhost:8000/callback
```

Create your local environment file:

```bash
cp .env.example .env
chmod 600 .env
```

Set at least:

```dotenv
BASECAMP_CLIENT_ID=your_oauth_client_id
BASECAMP_CLIENT_SECRET=your_oauth_client_secret
BASECAMP_REDIRECT_URI=http://localhost:8000/callback
BASECAMP_USER_AGENT=Basecamp MCP Server (you@example.com)
```

Authorize the application:

```bash
basecamp-oauth
```

Refresh an expired access token with:

```bash
basecamp-oauth --refresh
```

Test the connection:

```bash
basecamp-test
```

## Write safety

Mutation tools are not registered unless this variable is enabled:

```dotenv
BASECAMP_ENABLE_WRITE_TOOLS=true
```

Keep it `false` for read-only usage. Even when writes are enabled, do not add mutation tools to an MCP client's automatic approval list.

Preview-bound confirmation tokens default to five minutes:

```dotenv
BASECAMP_CONFIRMATION_TTL_SECONDS=300
```

The following Card Table writes require a valid preview token:

- `add_card_update` from `preview_card_update`
- `update_card_due_date` from `preview_card_due_date`
- `add_investigation_report_to_card` from `preview_investigation_report_to_card`

Other optional mutation tools still rely on `BASECAMP_ENABLE_WRITE_TOOLS=true` and the MCP host's approval controls.

## Kiro configuration

```json
{
  "mcpServers": {
    "basecamp": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/thiagorchaves/basecamp-mcp-server.git",
        "basecamp-mcp"
      ],
      "env": {
        "BASECAMP_ACCOUNT_ID": "${BASECAMP_ACCOUNT_ID}",
        "BASECAMP_ACCESS_TOKEN": "${BASECAMP_ACCESS_TOKEN}",
        "BASECAMP_USER_AGENT": "${BASECAMP_USER_AGENT}",
        "BASECAMP_ENABLE_WRITE_TOOLS": "false",
        "BASECAMP_CONFIRMATION_TTL_SECONDS": "300"
      },
      "autoApprove": []
    }
  }
}
```

## Tools

### Read-only and preview

- `healthcheck`
- `list_projects`, `find_projects`, `find_project_by_name`, `get_project`
- `get_project_tools`
- `list_messages`
- `list_todolists`, `list_project_todolists`, `list_todos`
- `list_project_todos`, `find_todos_by_title`
- `get_recording`
- `list_project_card_tables`, `get_card_table`, `list_cards`
- `find_cards_by_title`, `find_cards_by_assignee`, `get_my_cards`
- `preview_card_update`
- `preview_card_due_date`
- `preview_investigation_report_to_card`

### Write-enabled

- `create_message`, `create_project_message`
- `create_project_message_from_markdown`
- `create_todo`, `create_todo_from_markdown`
- `update_card_by_title`
- `add_comment`, `comment_recording_from_markdown`
- `add_card_update` (preview token required)
- `update_card_due_date` (preview token required)
- `add_investigation_report_to_card` (preview token required)

## Recommended card workflow

1. Find the project and target card.
2. Display its title, column, URL, and current state.
3. Call the appropriate preview tool.
4. Show the preview and ask the user for explicit confirmation.
5. Pass the returned `confirmation_id` to the matching write tool.
6. Read the resource again and report the final state.

## Development

```bash
uv sync --extra dev
uv run ruff format --check .
uv run ruff check .
uv run mypy basecamp_mcp
uv run pytest
```

CI tests Python 3.11, 3.12, and 3.13 and runs a scheduled dependency audit.

## Security

Never commit `.env`, OAuth tokens, account IDs from private environments, or real API responses containing people and project data. See [SECURITY.md](SECURITY.md) for vulnerability reporting.

## License

MIT. See [LICENSE](LICENSE).
