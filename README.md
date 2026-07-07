# Basecamp MCP Server

[Português (Brasil)](README.pt-BR.md)

An open-source Model Context Protocol server for Basecamp projects, messages,
to-dos, recordings, and Card Tables. It was designed for operational workflows
where an AI assistant needs to find work items, preview updates, and write back
only after explicit approval.

> [!IMPORTANT]
> This is an independent community project. It is not affiliated with,
> sponsored by, or endorsed by 37signals or Basecamp.

## Highlights

- Discover projects and enabled project tools.
- Search to-dos and Card Table cards by title or assignee.
- Follow Basecamp pagination automatically.
- Preview Card Table comments before writing.
- Add comments, investigation reports, and due dates to existing cards.
- Create messages and to-dos when write tools are explicitly enabled.
- Refuse ambiguous title-based writes when multiple items match.
- Keep every mutation tool disabled by default.

## Requirements

- Python 3.11 or newer.
- A Basecamp OAuth application.
- An MCP-compatible client such as Kiro, Claude Desktop, or another stdio host.

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

Register an application in the 37signals integrations console and use this
redirect URI:

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

The command stores the access token, refresh token, expiration timestamp, and,
when only one Basecamp account is available, the account ID in `.env`.

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

Keep it `false` for read-only usage. Even when writes are enabled, do not add
mutation tools to an MCP client's automatic approval list.

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
        "BASECAMP_ENABLE_WRITE_TOOLS": "false"
      },
      "autoApprove": []
    }
  }
}
```

Change `BASECAMP_ENABLE_WRITE_TOOLS` to `true` only for sessions that need to
modify Basecamp.

## Tools

### Read-only

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

### Write-enabled

- `create_message`, `create_project_message`
- `create_project_message_from_markdown`
- `create_todo`, `create_todo_from_markdown`
- `add_comment`, `comment_recording_from_markdown`, `comment_card`
- `update_card_by_title`, `update_card_table_card_by_title`
- `add_card_update`, `add_investigation_report_to_card`
- `update_card_due_date`

## Recommended agent workflow

1. Find the project and target card.
2. Display its title, column, URL, and current due date.
3. Call `preview_card_update`.
4. Ask the user for explicit confirmation.
5. Perform the write.
6. Read the resource again and report the final state.

## Development

```bash
uv sync --extra dev
uv run ruff format --check .
uv run ruff check .
uv run mypy basecamp_mcp
uv run pytest
```

## Security

Never commit `.env`, OAuth tokens, account IDs from private environments, or
real API responses containing people and project data. See [SECURITY.md](SECURITY.md)
for vulnerability reporting.

## License

MIT. See [LICENSE](LICENSE).
