"""
MCP-сервер с HTTP-транспортом для работы с Finam TradeAPI
"""

import requests
from fastmcp import FastMCP

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
def get_finam_quote(symbol: str) -> dict[str, str | int | float]:
    """
    Получает текущую котировку инструмента через Finam API
    
    Args:
        symbol: Тикер инструмента (например, "SBER@MISX")
        
    Returns:
        Словарь с информацией о котировке или ошибке
    """
    try:
        # Используем существующий FinamAPIClient
        from ..adapters.finam_client import FinamAPIClient
        
        client = FinamAPIClient()
        result = client.get_quote(symbol)
        
        return {
            "symbol": symbol,
            "data": result,
            "status": "success"
        }
        
    except Exception as e:
        return {
            "symbol": symbol,
            "status": "error",
            "message": f"Ошибка при получении котировки: {str(e)}"
        }


def main() -> None:
    """
    Точка входа для запуска MCP-сервера через HTTP
    """
    print("🚀 Запуск MCP-сервера в режиме HTTP...")
    print("📡 Сервер будет доступен по адресу: http://localhost:8765")
    print("🔗 MCP endpoint: http://localhost:8765/mcp")
    # print("📚 Документация: http://localhost:8765/docs")
    print("=" * 50)
    
    mcp.run(transport="http", host="0.0.0.0", port=8765)


if __name__ == "__main__":
    main()
