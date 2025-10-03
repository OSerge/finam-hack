"""
Расширенный MCP-сервер с поддержкой JWT токенов для работы с Finam TradeAPI
"""

import os
import requests
from dotenv import load_dotenv
from fastmcp import FastMCP

from ..adapters.finam_client_enhanced import FinamAPIClientEnhanced

# Загружаем переменные окружения из .env файла
load_dotenv()

mcp = FastMCP("Finam Trader MCP Server")


@mcp.tool()
def check_finam_api() -> dict[str, str | int]:
    """
    Проверяет доступность Finam API (https://api.finam.ru/v1)

    Returns:
        Словарь с информацией о доступности API:
        - status: "available" | "unavailable" | "error"
        - code: HTTP статус код (если доступен)
        - message: Сообщение об ошибке (если есть)
    """
    try:
        response = requests.get("https://api.finam.ru/v1", timeout=10)
        
        if response.status_code == 200:
            return {
                "status": "available",
                "code": response.status_code,
                "message": "API доступен",
            }
        else:
            return {
                "status": "unavailable",
                "code": response.status_code,
                "message": f"API вернул статус код {response.status_code}",
            }
    
    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "message": "Превышено время ожидания ответа от API",
        }
    
    except requests.exceptions.ConnectionError:
        return {
            "status": "error",
            "message": "Не удалось установить соединение с API",
        }
    
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": f"Ошибка при проверке доступности API: {str(e)}",
        }


@mcp.tool()
def get_jwt_token_details() -> dict[str, str | dict]:
    """
    Получить детали текущего JWT токена Finam API

    Returns:
        Словарь с информацией о JWT токене:
        - status: "success" | "error"
        - token_details: Детали токена (если успешно)
        - message: Сообщение о результате
    """
    try:
        client = FinamAPIClientEnhanced()
        result = client.get_jwt_token_details_sync()
        return result
    except Exception as e:
        return {
            "status": "error",
            "message": f"Ошибка при инициализации клиента: {str(e)}"
        }


@mcp.tool()
def refresh_jwt_token() -> dict[str, str]:
    """
    Обновить JWT токен Finam API

    Returns:
        Словарь с результатом обновления:
        - status: "success" | "error"
        - message: Сообщение о результате
    """
    try:
        client = FinamAPIClientEnhanced()
        result = client.refresh_jwt_token_sync()
        return result
    except Exception as e:
        return {
            "status": "error",
            "message": f"Ошибка при инициализации клиента: {str(e)}"
        }


@mcp.tool()
def get_finam_accounts() -> dict[str, str | list | dict]:
    """
    Получить список доступных счетов Finam

    Returns:
        Словарь со списком счетов:
        - status: "success" | "error"
        - accounts: Список счетов (если успешно)
        - message: Сообщение о результате
    """
    try:
        client = FinamAPIClientEnhanced()
        result = client.get_accounts_sync()
        return result
    except Exception as e:
        return {
            "status": "error",
            "message": f"Ошибка при инициализации клиента: {str(e)}"
        }


@mcp.tool()
def get_finam_portfolio(account_id: str) -> dict[str, str | dict]:
    """
    Получить портфель по счету Finam

    Args:
        account_id: Идентификатор счета

    Returns:
        Словарь с информацией о портфеле:
        - status: "success" | "error"
        - portfolio: Информация о портфеле (если успешно)
        - account_id: ID счета
        - message: Сообщение о результате
    """
    try:
        client = FinamAPIClientEnhanced()
        result = client.get_portfolio_sync(account_id)
        return result
    except Exception as e:
        return {
            "status": "error",
            "account_id": account_id,
            "message": f"Ошибка при инициализации клиента: {str(e)}"
        }


@mcp.tool()
def get_finam_quotes(symbol: str) -> dict[str, str | dict]:
    """
    Получить котировки инструмента через Finam API

    Args:
        symbol: Тикер инструмента (например, "SBER@MISX")

    Returns:
        Словарь с котировками:
        - status: "success" | "error"
        - quotes: Котировки (если успешно)
        - symbol: Тикер инструмента
        - message: Сообщение о результате
    """
    try:
        client = FinamAPIClientEnhanced()
        result = client.get_quotes_sync(symbol)
        return result
    except Exception as e:
        return {
            "status": "error",
            "symbol": symbol,
            "message": f"Ошибка при инициализации клиента: {str(e)}"
        }


@mcp.tool()
def search_finam_instruments(query: str = "") -> dict[str, str | list | dict]:
    """
    Поиск инструментов в Finam API

    Args:
        query: Поисковый запрос (например, "SBER")

    Returns:
        Словарь с найденными инструментами:
        - status: "success" | "error"
        - instruments: Список инструментов (если успешно)
        - query: Поисковый запрос
        - message: Сообщение о результате
    """
    try:
        client = FinamAPIClientEnhanced()
        result = client.get_instruments_sync(query)
        return result
    except Exception as e:
        return {
            "status": "error",
            "query": query,
            "message": f"Ошибка при инициализации клиента: {str(e)}"
        }


@mcp.tool()
def get_finam_orderbook(symbol: str, depth: int = 10) -> dict[str, str | dict | int]:
    """
    Получить стакан заявок для инструмента

    Args:
        symbol: Тикер инструмента (например, "SBER@MISX")
        depth: Глубина стакана (по умолчанию 10)

    Returns:
        Словарь со стаканом заявок:
        - status: "success" | "error"
        - orderbook: Стакан заявок (если успешно)
        - symbol: Тикер инструмента
        - depth: Глубина стакана
        - message: Сообщение о результате
    """
    try:
        client = FinamAPIClientEnhanced()
        result = client.get_orderbook_sync(symbol, depth)
        return result
    except Exception as e:
        return {
            "status": "error",
            "symbol": symbol,
            "depth": depth,
            "message": f"Ошибка при инициализации клиента: {str(e)}"
        }


@mcp.tool()
def get_finam_candles(
    symbol: str, 
    timeframe: str = "D", 
    start: str | None = None, 
    end: str | None = None
) -> dict[str, str | dict | list]:
    """
    Получить исторические свечи для инструмента

    Args:
        symbol: Тикер инструмента (например, "SBER@MISX")
        timeframe: Таймфрейм ("D" - день, "H" - час, "M" - минута)
        start: Начальная дата в формате ISO (например, "2024-01-01T00:00:00Z")
        end: Конечная дата в формате ISO (например, "2024-01-31T23:59:59Z")

    Returns:
        Словарь со свечами:
        - status: "success" | "error"
        - candles: Список свечей (если успешно)
        - symbol: Тикер инструмента
        - timeframe: Таймфрейм
        - message: Сообщение о результате
    """
    try:
        client = FinamAPIClientEnhanced()
        result = client.get_candles_sync(symbol, timeframe, start, end)
        return result
    except Exception as e:
        return {
            "status": "error",
            "symbol": symbol,
            "timeframe": timeframe,
            "message": f"Ошибка при инициализации клиента: {str(e)}"
        }


@mcp.tool()
def get_finam_orders(account_id: str) -> dict[str, str | dict | list]:
    """
    Получить список заявок по счету

    Args:
        account_id: Идентификатор счета

    Returns:
        Словарь со списком заявок:
        - status: "success" | "error"
        - orders: Список заявок (если успешно)
        - account_id: ID счета
        - message: Сообщение о результате
    """
    try:
        client = FinamAPIClientEnhanced()
        result = client.get_orders_sync(account_id)
        return result
    except Exception as e:
        return {
            "status": "error",
            "account_id": account_id,
            "message": f"Ошибка при инициализации клиента: {str(e)}"
        }


def main() -> None:
    """
    Точка входа для запуска расширенного MCP-сервера в HTTP режиме
    """
    PORT = 8765
    
    print("🚀 Запуск расширенного MCP-сервера в режиме HTTP...")
    print(f"📡 Сервер будет доступен по адресу: http://localhost:{PORT}")
    print(f"🔗 MCP endpoint: http://localhost:{PORT}/mcp")
    print("🔐 Поддержка автоматического обновления JWT токенов")
    print("📊 Доступные инструменты:")
    print("   - check_finam_api: Проверка доступности API")
    print("   - get_jwt_token_details: Получение деталей JWT токена")
    print("   - refresh_jwt_token: Обновление JWT токена")
    print("   - get_finam_accounts: Получение списка счетов")
    print("   - get_finam_portfolio: Получение портфеля")
    print("   - get_finam_quotes: Получение котировок")
    print("   - search_finam_instruments: Поиск инструментов")
    print("   - get_finam_orderbook: Получение стакана заявок")
    print("   - get_finam_candles: Получение исторических свечей")
    print("   - get_finam_orders: Получение списка заявок")
    print("=" * 60)
    
    mcp.run(transport="http", host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()