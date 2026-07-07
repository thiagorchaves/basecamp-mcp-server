# Basecamp MCP Server

Servidor open source de Model Context Protocol para projetos, mensagens,
tarefas, recordings e Card Tables do Basecamp. Ele foi pensado para fluxos
operacionais nos quais um assistente de IA localiza cards, gera previews e só
escreve depois de uma autorização explícita.

> [!IMPORTANT]
> Este é um projeto independente da comunidade. Ele não é afiliado, patrocinado
> ou endossado pela 37signals ou pelo Basecamp.

## Principais recursos

- Descoberta de projetos e ferramentas habilitadas.
- Busca de to-dos e cards por título ou responsável.
- Paginação automática da API.
- Preview de comentários antes da escrita.
- Comentários, relatórios de investigação e atualização de prazo.
- Criação de mensagens e to-dos quando a escrita é habilitada.
- Bloqueio de escrita quando mais de um item corresponde ao título.
- Ferramentas de escrita desligadas por padrão.

## Instalação

```bash
uv tool install git+https://github.com/thiagorchaves/basecamp-mcp-server.git
```

Para desenvolvimento:

```bash
git clone https://github.com/thiagorchaves/basecamp-mcp-server.git
cd basecamp-mcp-server
uv sync --extra dev
```

## OAuth do Basecamp

Registre uma aplicação na área de integrações da 37signals e configure:

```text
http://localhost:8000/callback
```

Prepare o ambiente:

```bash
cp .env.example .env
chmod 600 .env
```

Preencha:

```dotenv
BASECAMP_CLIENT_ID=seu_client_id
BASECAMP_CLIENT_SECRET=seu_client_secret
BASECAMP_REDIRECT_URI=http://localhost:8000/callback
BASECAMP_USER_AGENT=Basecamp MCP Server (voce@example.com)
```

Autorize:

```bash
basecamp-oauth
```

Renove um token expirado:

```bash
basecamp-oauth --refresh
```

Teste a conexão:

```bash
basecamp-test
```

## Escrita segura

As ferramentas que alteram o Basecamp só são registradas quando esta variável
está habilitada:

```dotenv
BASECAMP_ENABLE_WRITE_TOOLS=true
```

Mantenha `false` para leitura. Mesmo com escrita habilitada, deixe as tools de
mutação fora do `autoApprove` do cliente MCP.

## Configuração no Kiro

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

## Fluxo recomendado

1. Localize o projeto e o card.
2. Mostre título, coluna, URL e prazo atual.
3. Gere o preview com `preview_card_update`.
4. Peça confirmação explícita.
5. Execute a escrita.
6. Leia novamente o recurso e confirme o resultado.

## Desenvolvimento

```bash
uv sync --extra dev
uv run ruff format --check .
uv run ruff check .
uv run mypy basecamp_mcp
uv run pytest
```

## Licença

MIT. Consulte [LICENSE](LICENSE).
