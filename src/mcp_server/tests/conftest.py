"""
Pytest fixtures для тестирования MCP сервера
"""

import os
import pytest
from fastmcp import Client
from dotenv import load_dotenv

from ..server import mcp

# Загружаем реальные переменные окружения из .env
load_dotenv()


@pytest.fixture
async def mcp_client():
    """
    Создает in-memory MCP клиент для тестирования.
    
    Использует in-memory транспорт FastMCP - идеально для тестирования,
    так как не требует запуска отдельного процесса или сетевых соединений.
    
    ВАЖНО: Использует РЕАЛЬНЫЙ FINAM_ACCESS_TOKEN из .env файла!
    """
    client = Client(mcp)
    
    async with client:
        yield client


@pytest.fixture
def real_finam_token():
    """
    Проверяет наличие реального FINAM_ACCESS_TOKEN
    """
    token = os.getenv("FINAM_ACCESS_TOKEN")
    if not token or token == "test_token_12345":
        pytest.skip("FINAM_ACCESS_TOKEN не установлен в .env файле")
    return token


@pytest.fixture
def demo_account_id():
    """
    Получает демо-аккаунт из переменной окружения FINAM_DEMO_ACCOUNT_ID
    """
    account_id = os.getenv("FINAM_DEMO_ACCOUNT_ID")
    if not account_id:
        pytest.skip("FINAM_DEMO_ACCOUNT_ID не установлен в .env файле")
    return account_id

