# Тесты MCP Сервера Finam API

Простые тесты с **реальными запросами** к Finam API через MCP сервер.

## Структура тестов

**Все тесты в `test_real_api.py` выполняются с реальными запросами к Finam API:**

- ✅ `test_api_health_check` - проверяет доступность API Finam
- ✅ `test_get_token` - получает/проверяет JWT токен
- ✅ `test_crypto_market` - тестирует получение криптовалют
- ✅ `test_search_instruments` - ищет инструменты по коду SBER
- ✅ `test_get_hourly_candles` - получает часовые свечи SBER за 2 дня
- ✅ `test_get_portfolio` - получение портфеля демо-аккаунта
- ✅ `test_get_quotes` - получение последних котировок SBER
- ✅ `test_get_orderbook` - получение стакана заявок SBER
- ✅ `test_get_candles` - получение дневных свечей SBER за неделю

## Запуск тестов

```bash
# Все тесты
poetry run pytest src/mcp_server/tests/test_real_api.py -v

# Конкретный тест
poetry run pytest src/mcp_server/tests/test_real_api.py::TestRealAPIWithAccounts::test_get_portfolio -v -s
```

## Требования

- Python 3.13+
- Poetry для управления зависимостями
- Активный MCP сервер в отдельном терминале

### Уключение зависимостей

```bash
cd /home/serge/Dev/finam-hack
poetry install
```

### Запуск MCP сервера

```bash
cd /home/serge/Dev/finam-hack
poetry run python -m src.mcp_server.server
```

## Настройка переменных окружения

Добавьте в `.env` файл:

```bash
# Finam API токен
FINAM_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." # ПОМЕНЯТЬ НА РЕАЛЬНЫЙ

# Демо-аккаунт для тестов торговых операций
FINAM_DEMO_ACCOUNT_ID="TRQD05:157..."
```

**❗ Важно:**
- Настоящий `FINAM_TOKEN` для всех тестов
- Демо-аккаунт безопасен для тестирования торговли
- Тесты автоматически пропускаются без токена

## Структура теста

```python
async def test_example(mcp_client, real_finam_token):
    """Тест API через Finam"""
    result = await mcp_client.call_tool("get_finam_quotes", {"symbol": "SBER@MISX"})
    print(f"\n✅ {result.data}")
    assert "status" in result.data
```

Файл использует:
- ✅ In-memory transport FastMCP для максимальной скорости
- ✅ Реальные запросы к Finam API через MCP сервер
- ✅ Простые ассерты на структуру ответа

## Улучшение архитектуры

В результате улучшений:
- ✅ Максимальный coverage с минимальным, но читаемым кодом
- ✅ Использование переменных окружения для демо-аккаунта
- ✅ Простота отладки: единый набор тестов для всех инструментов
- ✅ Максимальная гибкость без сложности, простота и эффективность

