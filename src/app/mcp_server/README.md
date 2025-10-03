# Finam Trader MCP Server

MCP-сервер для работы с Finam TradeAPI через HTTP транспорт.

## 🚀 Запуск

```bash
# Стандартный запуск (порт 8765)
poetry run mcp-server

# Или напрямую
poetry run python -m src.app.mcp_server.server
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

- `check_finam_api` - проверка доступности API
- `get_jwt_token_details` - детали JWT токена
- `refresh_jwt_token` - обновление JWT токена
- `get_finam_accounts` - список счетов
- `get_finam_portfolio` - портфель
- `get_finam_quotes` - котировки
- `search_finam_instruments` - поиск инструментов
- `get_finam_orderbook` - стакан заявок
- `get_finam_candles` - исторические свечи
- `get_finam_orders` - список заявок

## 🔐 Настройка токена

Убедитесь, что в файле `.env` установлен:
```
FINAM_TOKEN=your_secret_token_here
```

## 📡 Доступ

- **HTTP Endpoint**: `http://localhost:8765/mcp`
- **Транспорт**: HTTP с Server-Sent Events
- **Протокол**: MCP (Model Context Protocol)

## 💡 Использование

После настройки в Cursor используйте инструменты через MCP панель или запрашивайте у AI-ассистента выполнение операций с Finam API.
