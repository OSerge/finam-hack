from typing import Any

import requests

from .config import get_settings


def call_llm(messages: list[dict[str, str]], temperature: float = 0.2, max_tokens: int | None = None) -> dict[str, Any]:
    """Простой вызов LLM без tools"""
    s = get_settings()
    payload: dict[str, Any] = {
        "model": s.openrouter_model,
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens:
        payload["max_tokens"] = max_tokens

    r = requests.post(
        f"{s.openrouter_base}/chat/completions",
        headers={
            "Authorization": f"Bearer {s.openrouter_api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=60,
    )
    r.raise_for_status()
    return r.json()


def call_llm_with_tools(
    messages: list[dict[str, Any]], 
    tools: list[dict[str, Any]], 
    temperature: float = 0.2, 
    max_tokens: int | None = None
) -> dict[str, Any]:
    """
    Вызов LLM с поддержкой function calling
    
    Args:
        messages: История сообщений
        tools: Список инструментов в формате OpenAI
        temperature: Температура генерации
        max_tokens: Максимальное количество токенов
        
    Returns:
        Ответ от LLM с возможными tool_calls
    """
    s = get_settings()
    payload: dict[str, Any] = {
        "model": s.openrouter_model,
        "messages": messages,
        "temperature": temperature,
        "tools": tools,
        "tool_choice": "auto",
    }
    if max_tokens:
        payload["max_tokens"] = max_tokens

    r = requests.post(
        f"{s.openrouter_base}/chat/completions",
        headers={
            "Authorization": f"Bearer {s.openrouter_api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=60,
    )
    r.raise_for_status()
    return r.json()
