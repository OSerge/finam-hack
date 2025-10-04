#!/usr/bin/env python3
"""
Streamlit веб-интерфейс для AI ассистента трейдера с поддержкой MCP tools

Использование:
    poetry run streamlit run src/app/chat_app.py
    streamlit run src/app/chat_app.py
"""

import asyncio
import json
from typing import Any

import streamlit as st

from src.app.core import MCPClient, call_llm_with_tools, get_settings


def _old_system_prompt() -> str:
    """Создать системный промпт для AI ассистента"""
    return """Ты - AI ассистент трейдера, работающий с Finam TradeAPI.

Когда пользователь задает вопрос о рынке, портфеле или хочет совершить действие:
1. Определи нужный API endpoint
2. Укажи запрос в формате: API_REQUEST: METHOD /path
3. После получения данных - проанализируй их и дай понятный ответ

Доступные endpoints:
- GET /v1/instruments/{symbol}/quotes/latest - котировка
- GET /v1/instruments/{symbol}/orderbook - стакан
- GET /v1/instruments/{symbol}/bars - свечи
- GET /v1/accounts/{account_id} - счет и позиции
- GET /v1/accounts/{account_id}/orders - ордера
- POST /v1/accounts/{account_id}/orders - создать ордер
- DELETE /v1/accounts/{account_id}/orders/{order_id} - отменить ордер

Отвечай на русском, кратко и по делу."""

def create_system_prompt() -> str:
    """Создать системный промпт для AI ассистента"""
    return """Ты - AI ассистент трейдера, работающий с Finam TradeAPI.

У тебя есть доступ к различным инструментам для работы с биржевыми данными:
- Получение котировок и стаканов заявок
- Просмотр портфеля и счетов
- Поиск инструментов
- Получение исторических данных (свечей)
- Просмотр активных заявок

Используй доступные инструменты для получения актуальной информации.
Отвечай на русском языке, кратко и по делу.
Анализируй полученные данные и давай полезные инсайты."""


async def execute_tool_calls(
    mcp_url: str,
    tool_calls: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """
    Выполнить вызовы инструментов через MCP клиент
    
    Args:
        mcp_url: URL MCP сервера
        tool_calls: Список вызовов инструментов от LLM
        
    Returns:
        Список результатов выполнения
    """
    results = []
    
    async with MCPClient(base_url=mcp_url) as client:
        for tool_call in tool_calls:
            tool_name = tool_call["function"]["name"]
            
            try:
                if isinstance(tool_call["function"]["arguments"], str):
                    arguments = json.loads(tool_call["function"]["arguments"])
                else:
                    arguments = tool_call["function"]["arguments"]
            except json.JSONDecodeError:
                arguments = {}
            
            try:
                result = await client.call_tool(tool_name, arguments)
                results.append({
                    "tool_call_id": tool_call["id"],
                    "role": "tool",
                    "name": tool_name,
                    "content": json.dumps(result, ensure_ascii=False)
                })
            except Exception as e:
                results.append({
                    "tool_call_id": tool_call["id"],
                    "role": "tool",
                    "name": tool_name,
                    "content": json.dumps({"error": str(e)}, ensure_ascii=False)
                })
    
    return results


def main() -> None:  # noqa: C901
    """Главная функция Streamlit приложения"""
    st.set_page_config(page_title="AI Трейдер (Finam)", page_icon="🤖", layout="wide")

    # Заголовок
    st.title("🤖 AI Ассистент Трейдера")
    st.caption("Интеллектуальный помощник с доступом к Finam TradeAPI через MCP")

    # Sidebar с настройками
    with st.sidebar:
        st.header("⚙️ Настройки")
        settings = get_settings()
        st.info(f"**Модель:** {settings.openrouter_model}")

        with st.expander("🔌 MCP Сервер", expanded=False):
            mcp_url = st.text_input(
                "MCP Server URL",
                value="http://mcp-server:8765",
                help="URL MCP сервера (в Docker: mcp-server:8765, локально: localhost:8765)"
            )

        if st.button("🔄 Очистить историю"):
            st.session_state.messages = []
            st.session_state.tools_loaded = False
            st.rerun()

        st.markdown("---")
        st.markdown("### 💡 Примеры вопросов:")
        st.markdown("""
        - Какая цена Сбербанка?
        - Покажи мой портфель
        - Что в стакане по Газпрому?
        - Найди инструменты по запросу YNDX
        - Покажи свечи SBER за последние дни
        - Какие у меня активные ордера?
        - Список всех доступных инструментов
        """)

    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "tools_loaded" not in st.session_state:
        st.session_state.tools_loaded = False
        st.session_state.tools = []

    # Загрузка tools при первом запуске
    if not st.session_state.tools_loaded:
        with st.spinner("🔄 Загрузка инструментов из MCP сервера..."):
            try:
                async def load_tools():
                    async with MCPClient(base_url=mcp_url) as client:
                        return await client.get_openai_tools()
                
                tools = asyncio.run(load_tools())
                st.session_state.tools = tools
                st.session_state.tools_loaded = True
                st.sidebar.success(f"✅ Загружено {len(tools)} инструментов")
            except Exception as e:
                st.sidebar.error(f"❌ Ошибка подключения к MCP серверу: {e}")
                st.sidebar.info("💡 Убедитесь, что MCP сервер запущен")

    # Отображение доступных инструментов
    if st.session_state.tools_loaded and st.sidebar.checkbox("📋 Показать доступные инструменты", value=False):
        with st.sidebar.expander("🛠️ Доступные инструменты", expanded=True):
            for tool in st.session_state.tools:
                func = tool["function"]
                st.markdown(f"**{func['name']}**")
                st.caption(func.get("description", "Нет описания"))

    # Отображение истории сообщений
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            # Показываем вызовы инструментов
            if "tool_calls" in message and message["tool_calls"]:
                with st.expander("🔧 Вызовы инструментов"):
                    for tc in message["tool_calls"]:
                        func_name = tc["function"]["name"]
                        try:
                            args = json.loads(tc["function"]["arguments"]) if isinstance(tc["function"]["arguments"], str) else tc["function"]["arguments"]
                            st.code(f"{func_name}({json.dumps(args, ensure_ascii=False, indent=2)})", language="python")
                        except:
                            st.code(f"{func_name}(...)", language="python")

    # Поле ввода
    if prompt := st.chat_input("Напишите ваш вопрос..."):
        if not st.session_state.tools_loaded:
            st.error("❌ Инструменты не загружены. Проверьте подключение к MCP серверу.")
            return

        # Добавляем сообщение пользователя
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Формируем историю для LLM
        conversation_history = [{"role": "system", "content": create_system_prompt()}]
        for msg in st.session_state.messages:
            # Добавляем только основные поля для истории
            history_msg = {"role": msg["role"], "content": msg["content"]}
            
            # Для assistant с tool_calls добавляем их
            if msg["role"] == "assistant" and "tool_calls" in msg:
                history_msg["tool_calls"] = msg["tool_calls"]
            
            conversation_history.append(history_msg)

        # Получаем ответ от ассистента
        with st.chat_message("assistant"), st.spinner("Думаю..."):
            try:
                max_iterations = 5
                iteration = 0
                
                while iteration < max_iterations:
                    iteration += 1
                    
                    # Вызываем LLM с tools
                    response = call_llm_with_tools(
                        conversation_history, 
                        st.session_state.tools,
                        temperature=0.3
                    )
                    
                    assistant_message = response["choices"][0]["message"]
                    
                    # Проверяем наличие tool_calls
                    if "tool_calls" in assistant_message and assistant_message["tool_calls"]:
                        # Показываем что выполняем инструменты
                        tool_names = [tc["function"]["name"] for tc in assistant_message["tool_calls"]]
                        st.info(f"🔧 Выполняю: {', '.join(tool_names)}")
                        
                        # Выполняем tool calls
                        tool_results = asyncio.run(
                            execute_tool_calls(mcp_url, assistant_message["tool_calls"])
                        )
                        
                        # Показываем результаты
                        with st.expander("📊 Результаты инструментов", expanded=False):
                            for result in tool_results:
                                st.markdown(f"**{result['name']}:**")
                                try:
                                    result_data = json.loads(result["content"])
                                    st.json(result_data)
                                except:
                                    st.text(result["content"])
                        
                        # Добавляем в историю
                        conversation_history.append({
                            "role": "assistant",
                            "content": assistant_message.get("content") or "",
                            "tool_calls": assistant_message["tool_calls"]
                        })
                        
                        for result in tool_results:
                            conversation_history.append(result)
                        
                        # Продолжаем цикл для получения финального ответа
                        continue
                    
                    # Если нет tool_calls, значит получили финальный ответ
                    final_content = assistant_message.get("content", "")
                    
                    if final_content:
                        st.markdown(final_content)
                        
                        # Сохраняем сообщение ассистента
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": final_content
                        })
                    
                    break
                
                if iteration >= max_iterations:
                    st.warning("⚠️ Достигнуто максимальное количество итераций")

            except Exception as e:
                st.error(f"❌ Ошибка: {e}")
                if settings.debug:
                    st.exception(e)


if __name__ == "__main__":
    main()
