"""
MCP клиент для взаимодействия с MCP сервером через FastMCP Client
"""

import json
from typing import Any

from fastmcp import Client


class MCPClient:
    """Клиент для работы с MCP сервером через FastMCP"""

    def __init__(self, base_url: str = "http://mcp-server:8765"):
        """
        Args:
            base_url: Базовый URL MCP сервера (для HTTP транспорта)
        """
        self.base_url = base_url
        # FastMCP Client автоматически определяет транспорт по URL
        self._client = Client(f"{base_url}/mcp", timeout=60.0)
        self._tools_cache: list[dict[str, Any]] | None = None
        self._connected = False

    async def __aenter__(self):
        """Вход в async context manager"""
        await self._client.__aenter__()
        self._connected = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Выход из async context manager"""
        self._connected = False
        return await self._client.__aexit__(exc_type, exc_val, exc_tb)

    def is_connected(self) -> bool:
        """Проверить, установлено ли соединение"""
        return self._connected

    async def list_tools(self) -> list[dict[str, Any]]:
        """
        Получить список доступных инструментов от MCP сервера
        
        Returns:
            Список инструментов в формате MCP
        """
        if self._tools_cache is not None:
            return self._tools_cache

        # FastMCP Client возвращает объекты Tool
        tools_response = await self._client.list_tools()
        
        # Преобразуем в dict формат
        self._tools_cache = []
        for tool in tools_response:
            tool_dict = {
                "name": tool.name,
                "description": tool.description or "",
            }
            if hasattr(tool, "inputSchema"):
                tool_dict["inputSchema"] = tool.inputSchema
            self._tools_cache.append(tool_dict)
        
        return self._tools_cache

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """
        Вызвать инструмент на MCP сервере
        
        Args:
            tool_name: Имя инструмента
            arguments: Аргументы для вызова
            
        Returns:
            Результат выполнения инструмента
        """
        # FastMCP Client возвращает CallToolResult
        result = await self._client.call_tool(tool_name, arguments)
        
        # result.content содержит список TextContent/ImageContent объектов
        if result.content:
            # Берем первый элемент (обычно text)
            first_content = result.content[0]
            if hasattr(first_content, "text"):
                text_content = first_content.text
                # Пытаемся распарсить JSON
                try:
                    return json.loads(text_content)
                except (json.JSONDecodeError, TypeError):
                    return text_content
            return first_content
        
        # Если нет content, возвращаем сам результат
        return result

    def convert_to_openai_tools(self, mcp_tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Преобразовать инструменты MCP в формат OpenAI function calling
        
        Args:
            mcp_tools: Список инструментов в формате MCP
            
        Returns:
            Список инструментов в формате OpenAI
        """
        openai_tools = []
        
        for tool in mcp_tools:
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                }
            }
            
            # Преобразуем inputSchema в parameters для OpenAI
            if "inputSchema" in tool:
                openai_tool["function"]["parameters"] = tool["inputSchema"]
            
            openai_tools.append(openai_tool)
        
        return openai_tools

    async def get_openai_tools(self) -> list[dict[str, Any]]:
        """
        Получить инструменты в формате OpenAI function calling
        
        Returns:
            Список инструментов в формате OpenAI
        """
        mcp_tools = await self.list_tools()
        return self.convert_to_openai_tools(mcp_tools)

