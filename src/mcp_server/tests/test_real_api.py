"""
Реальные интеграционные тесты MCP сервера с Finam API

ВАЖНО: 
- Эти тесты отправляют РЕАЛЬНЫЕ запросы к Finam API!
- Используют демо-аккаунт из FINAM_DEMO_ACCOUNT_ID в .env (безопасно!)
- Требуют FINAM_ACCESS_TOKEN в .env файле
"""

import pytest


pytestmark = pytest.mark.asyncio


class TestRealAPI:
    """Простые тесты с реальными запросами к Finam API"""

    async def test_check_api_availability(self, mcp_client):
        """Проверка доступности Finam API"""
        result = await mcp_client.call_tool("check_finam_api", {})
        
        print(f"\n✅ API Status: {result.data}")
        assert result.data["status"] in ["available", "unavailable", "error"]

    async def test_get_jwt_token(self, mcp_client, real_finam_token):
        """Получение JWT токена"""
        result = await mcp_client.call_tool("get_jwt_token_details", {})
        
        print(f"\n✅ JWT Token: {result.data}")
        assert "status" in result.data
        assert "message" in result.data

    async def test_refresh_jwt_token(self, mcp_client, real_finam_token):
        """Обновление JWT токена"""
        result = await mcp_client.call_tool("refresh_jwt_token", {})
        
        print(f"\n✅ Refresh Token: {result.data}")
        assert "status" in result.data
        assert "message" in result.data

    async def test_get_accounts(self, mcp_client, real_finam_token):
        """Получение списка счетов"""
        result = await mcp_client.call_tool("get_finam_accounts", {})
        
        print(f"\n✅ Accounts: {result.data}")
        assert "status" in result.data
        assert "message" in result.data

    async def test_search_instruments(self, mcp_client, real_finam_token):
        """Поиск инструмента SBER"""
        result = await mcp_client.call_tool(
            "search_finam_instruments",
            {"query": "SBER"}
        )
        
        print(f"\n✅ Search SBER: {result.data}")
        assert "status" in result.data

    async def test_get_quotes(self, mcp_client, real_finam_token):
        """Получение котировок SBER"""
        result = await mcp_client.call_tool(
            "get_finam_quotes",
            {"symbol": "SBER@MISX"}
        )
        
        print(f"\n✅ Quotes SBER: {result.data}")
        assert "status" in result.data

    async def test_get_orderbook(self, mcp_client, real_finam_token):
        """Получение стакана заявок SBER"""
        result = await mcp_client.call_tool(
            "get_finam_orderbook",
            {"symbol": "SBER@MISX", "depth": 5}
        )
        
        print(f"\n✅ Orderbook SBER: {result.data}")
        assert "status" in result.data

    async def test_get_candles(self, mcp_client, real_finam_token):
        """Получение исторических свечей SBER"""
        result = await mcp_client.call_tool(
            "get_finam_candles",
            {
                "symbol": "SBER@MISX",
                "timeframe": "D",
                "start": "2024-01-01T00:00:00Z",
                "end": "2024-01-10T23:59:59Z"
            }
        )
        
        print(f"\n✅ Candles SBER: {result.data}")
        assert "status" in result.data

    async def test_get_assets(self, mcp_client, real_finam_token):
        """Получение списка всех доступных активов"""
        result = await mcp_client.call_tool("get_finam_assets", {})
        
        print(f"\n✅ Assets: {result.data.get('message', result.data)}")
        assert "status" in result.data

    async def test_full_workflow(self, mcp_client, real_finam_token):
        """
        Полный workflow:
        1. Проверка API
        2. Поиск инструмента
        3. Получение котировок
        """
        # 1. Проверяем API
        api_check = await mcp_client.call_tool("check_finam_api", {})
        print(f"\n1️⃣ API Check: {api_check.data['status']}")
        
        # 2. Ищем SBER
        search = await mcp_client.call_tool(
            "search_finam_instruments",
            {"query": "SBER"}
        )
        print(f"2️⃣ Search SBER: {search.data['status']}")
        
        # 3. Получаем котировки
        quotes = await mcp_client.call_tool(
            "get_finam_quotes",
            {"symbol": "SBER@MISX"}
        )
        print(f"3️⃣ Get Quotes: {quotes.data['status']}")
        
        assert api_check.data["status"] in ["available", "unavailable", "error"]
        assert "status" in search.data
        assert "status" in quotes.data

    async def test_get_orderbook_depth_limit(self, mcp_client, real_finam_token):
        """Проверка, что глубина стакана ограничивается."""

        depth = 3
        result = await mcp_client.call_tool(
            "get_finam_orderbook",
            {"symbol": "SBER@MISX", "depth": depth},
        )

        print(f"\n✅ Depth-limited orderbook: {result.data}")
        assert result.data["status"] == "success"
        rows = result.data["orderbook"]["orderbook"].get("rows", [])
        assert len(rows) <= depth

    async def test_get_assets_payload(self, mcp_client, real_finam_token):
        """Проверка, что получаем список активов."""

        result = await mcp_client.call_tool("get_finam_assets", {})

        print(f"\n✅ Assets payload: {result.data}")
        assert result.data["status"] == "success"
        assets = result.data.get("assets")
        assert isinstance(assets, list)
        assert assets


class TestRealAPIWithAccounts:
    """Тесты с демо-аккаунтом из .env"""

    async def test_get_portfolio(self, mcp_client, real_finam_token, demo_account_id):
        """Получение портфеля демо-аккаунта"""
        print(f"\n🏦 Используется демо-аккаунт: {demo_account_id}")
        
        result = await mcp_client.call_tool(
            "get_finam_portfolio",
            {"account_id": demo_account_id}
        )
        
        print(f"\n✅ Portfolio: {result.data}")
        assert "status" in result.data

    async def test_get_orders(self, mcp_client, real_finam_token, demo_account_id):
        """Получение заявок демо-аккаунта"""
        print(f"\n🏦 Используется демо-аккаунт: {demo_account_id}")
        
        result = await mcp_client.call_tool(
            "get_finam_orders",
            {"account_id": demo_account_id}
        )
        
        print(f"\n✅ Orders: {result.data}")
        assert "status" in result.data

