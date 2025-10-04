# Finam Trader MCP Server

MCP-сервер для работы с Finam TradeAPI через HTTP транспорт.

## 🚀 Запуск

```bash
# Стандартный запуск (порт 8765)
poetry run mcp-server

# Или напрямую
poetry run python -m src.mcp_server.server
```

## 🔧 Настройка в Cursor IDE

1. **Добавьте в `~/.cursor/mcp.json`:**
```json
{
  "mcpServers": {
    "finam-trader": {
      "transportType": "http",
      "url": "http://localhost:8765/mcp"
    }
  }
}
```

2. **Перезапустите Cursor**

3. **Проверьте MCP панель** - должен появиться сервер `finam-trader`

## 🛠️ Доступные инструменты

**Все инструменты поддерживают нативный async/await!**

- `check_finam_api` - проверка доступности API (async)
- `get_jwt_token_details` - детали JWT токена (async)
- `refresh_jwt_token` - обновление JWT токена (async)
- `get_finam_accounts` - список счетов (async)
- `get_finam_portfolio` - портфель (async)
- `get_finam_quotes` - котировки (async)
- `search_finam_instruments` - поиск инструментов (async)
- `get_finam_orderbook` - стакан заявок (async)
- `get_finam_candles` - исторические свечи (async)
- `get_finam_orders` - список заявок (async)
- `get_finam_assets` - список всех активов (async)

## 🔐 Настройка токена

Убедитесь, что в файле `.env` установлен:
```
FINAM_ACCESS_TOKEN=your_secret_token_here
```

## 📡 Доступ

- **HTTP Endpoint**: `http://localhost:8765/mcp`
- **Транспорт**: HTTP с Server-Sent Events
- **Протокол**: MCP (Model Context Protocol)
