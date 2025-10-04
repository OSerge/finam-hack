#!/usr/bin/env python3
"""
Скрипт для генерации submission.csv на основе test.csv с использованием MCP tools

Использует LLM + MCP tools для преобразования вопросов на естественном языке
в HTTP запросы к Finam TradeAPI с возможностью вызова инструментов для
получения контекста (поиск инструментов, проверка символов и т.д.)

Использование:
    python scripts/generate_submission_adv.py [OPTIONS]

Опции:
    --test-file PATH      Путь к test.csv (по умолчанию: data/processed/test.csv)
    --train-file PATH     Путь к train.csv (по умолчанию: data/processed/train.csv)
    --output-file PATH    Путь к submission.csv (по умолчанию: data/processed/submission.csv)
    --num-examples INT    Количество примеров для few-shot (по умолчанию: 10)
    --mcp-url URL         URL MCP сервера (по умолчанию: http://localhost:8765)
    --use-mcp/--no-mcp    Использовать MCP tools (по умолчанию: True)
    --max-iterations INT  Максимальное количество итераций tool calling (по умолчанию: 3)
"""

import asyncio
import csv
import json
import random
from pathlib import Path
from typing import Any

import click
from tqdm import tqdm  # type: ignore[import-untyped]

from src.app.core.llm import call_llm, call_llm_with_tools
from src.app.core.mcp_client import MCPClient


def calculate_cost(usage: dict, model: str) -> float:
    """Рассчитать стоимость запроса на основе usage и модели"""
    # Цены OpenRouter (примерные, в $ за 1M токенов)
    # Источник: https://openrouter.ai/models
    pricing = {
        "openai/gpt-4o-mini": {"prompt": 0.15, "completion": 0.60},
        "openai/gpt-4o": {"prompt": 2.50, "completion": 10.00},
        "openai/gpt-3.5-turbo": {"prompt": 0.50, "completion": 1.50},
        "anthropic/claude-3-sonnet": {"prompt": 3.00, "completion": 15.00},
        "anthropic/claude-3-haiku": {"prompt": 0.25, "completion": 1.25},
    }

    # Получаем цены для модели (по умолчанию как для gpt-4o-mini)
    prices = pricing.get(model, {"prompt": 0.15, "completion": 0.60})

    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)

    # Считаем стоимость (цена за 1M токенов)
    prompt_cost = (prompt_tokens / 1_000_000) * prices["prompt"]
    completion_cost = (completion_tokens / 1_000_000) * prices["completion"]

    return prompt_cost + completion_cost


def load_train_examples(train_file: Path, num_examples: int = 10) -> list[dict[str, str]]:
    """Загрузить примеры из train.csv для few-shot learning"""
    examples = []
    with open(train_file, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            examples.append({"question": row["question"], "type": row["type"], "request": row["request"]})

    # Берем разнообразные примеры (GET, POST, DELETE)
    get_examples = [e for e in examples if e["type"] == "GET"]
    post_examples = [e for e in examples if e["type"] == "POST"]
    delete_examples = [e for e in examples if e["type"] == "DELETE"]

    # Формируем сбалансированный набор
    selected = []
    selected.extend(random.sample(get_examples, min(num_examples - 3, len(get_examples))))
    selected.extend(random.sample(post_examples, min(2, len(post_examples))))
    selected.extend(random.sample(delete_examples, min(1, len(delete_examples))))

    return selected[:num_examples]


def create_prompt(question: str, examples: list[dict[str, str]]) -> str:
    """Создать промпт для LLM с few-shot примерами"""
    prompt = """Ты - эксперт по Finam TradeAPI. Твоя задача - преобразовать вопрос на русском языке в HTTP запрос к API.

API Documentation:
- GET /v1/exchanges - список бирж
- GET /v1/assets - поиск инструментов
- GET /v1/assets/{symbol} - информация об инструменте
- GET /v1/assets/{symbol}/params - параметры инструмента для счета
- GET /v1/assets/{symbol}/schedule - расписание торгов
- GET /v1/assets/{symbol}/options - опционы на базовый актив
- GET /v1/instruments/{symbol}/quotes/latest - последняя котировка
- GET /v1/instruments/{symbol}/orderbook - биржевой стакан
- GET /v1/instruments/{symbol}/trades/latest - лента сделок
- GET /v1/instruments/{symbol}/bars - исторические свечи
  (параметры: timeframe, interval.start_time, interval.end_time)
- GET /v1/accounts/{account_id} - информация о счете
- GET /v1/accounts/{account_id}/orders - список ордеров
- GET /v1/accounts/{account_id}/orders/{order_id} - информация об ордере
- GET /v1/accounts/{account_id}/trades - история сделок
- GET /v1/accounts/{account_id}/transactions - транзакции по счету
- POST /v1/sessions - создание новой сессии
- POST /v1/sessions/details - детали текущей сессии
- POST /v1/accounts/{account_id}/orders - создание ордера
- DELETE /v1/accounts/{account_id}/orders/{order_id} - отмена ордера

Timeframes: TIME_FRAME_M1, TIME_FRAME_M5, TIME_FRAME_M15, TIME_FRAME_M30,
TIME_FRAME_H1, TIME_FRAME_H4, TIME_FRAME_D, TIME_FRAME_W, TIME_FRAME_MN

Примеры:

"""

    for ex in examples:
        prompt += f'Вопрос: "{ex["question"]}"\n'
        prompt += f"Ответ: {ex['type']} {ex['request']}\n\n"

    prompt += f'Вопрос: "{question}"\n'
    prompt += "Ответ (только HTTP метод и путь, без объяснений):"

    return prompt


def create_system_prompt_with_tools() -> str:
    """Системный промпт для работы с MCP tools"""
    return """Ты - эксперт по Finam TradeAPI. Твоя задача - преобразовать вопрос на русском языке в HTTP запрос к API.

У тебя есть доступ к инструментам для:
- Поиска торговых инструментов (search_finam_instruments)
- Получения списка всех инструментов (get_finam_assets)
- Получения котировок (get_finam_quotes)
- Получения стакана заявок (get_finam_orderbook)

ВАЖНО: Используй инструменты ТОЛЬКО если:
1. Нужно найти точный символ инструмента (например, "Сбербанк" -> "SBER@MISX")
2. Нужно проверить существование инструмента
3. Вопрос неоднозначный и требует дополнительного контекста

После получения контекста, сформируй ФИНАЛЬНЫЙ ОТВЕТ в формате:
HTTP_METHOD /path

Например:
GET /v1/instruments/SBER@MISX/quotes/latest
POST /v1/accounts/{account_id}/orders
DELETE /v1/accounts/{account_id}/orders/ORD123

API Documentation:
- GET /v1/exchanges - список бирж
- GET /v1/assets - поиск инструментов
- GET /v1/assets/{symbol} - информация об инструменте
- GET /v1/instruments/{symbol}/quotes/latest - последняя котировка
- GET /v1/instruments/{symbol}/orderbook - биржевой стакан
- GET /v1/instruments/{symbol}/trades/latest - лента сделок
- GET /v1/instruments/{symbol}/bars - исторические свечи
- GET /v1/accounts/{account_id} - информация о счете
- GET /v1/accounts/{account_id}/orders - список ордеров
- GET /v1/accounts/{account_id}/orders/{order_id} - информация об ордере
- POST /v1/sessions - создание новой сессии
- POST /v1/accounts/{account_id}/orders - создание ордера
- DELETE /v1/accounts/{account_id}/orders/{order_id} - отмена ордера"""


def parse_llm_response(response: str) -> tuple[str, str]:
    """Парсинг ответа LLM в (type, request)"""
    response = response.strip()

    # Ищем HTTP метод в начале
    methods = ["GET", "POST", "DELETE", "PUT", "PATCH"]
    method = "GET"  # по умолчанию
    request = response

    for m in methods:
        if response.upper().startswith(m):
            method = m
            request = response[len(m) :].strip()
            break

    # Убираем лишние символы
    request = request.strip()
    if not request.startswith("/"):
        # Если LLM вернул что-то странное, пытаемся найти путь
        parts = request.split()
        for part in parts:
            if part.startswith("/"):
                request = part
                break

    # Fallback на безопасный вариант
    if not request.startswith("/"):
        request = "/v1/assets"

    return method, request


async def execute_tool_calls(
    mcp_url: str,
    tool_calls: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Выполнить tool calls через MCP client"""
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


async def generate_api_call_with_mcp(
    question: str,
    examples: list[dict[str, str]],
    tools: list[dict[str, Any]],
    mcp_url: str,
    model: str,
    max_iterations: int = 3
) -> tuple[dict[str, str], float]:
    """
    Сгенерировать API запрос с использованием MCP tools

    Returns:
        tuple: (result_dict, cost_in_dollars)
    """
    # Создаем промпт с few-shot примерами
    few_shot_examples = "\n\nПримеры:\n\n"
    for ex in examples:
        few_shot_examples += f'Вопрос: "{ex["question"]}"\n'
        few_shot_examples += f"Ответ: {ex['type']} {ex['request']}\n\n"

    user_prompt = f"""{few_shot_examples}

Вопрос: "{question}"

Проанализируй вопрос и сформируй HTTP запрос к Finam API.
Используй инструменты для поиска, если нужно уточнить символ инструмента.
После сбора контекста дай ФИНАЛЬНЫЙ ОТВЕТ в формате: HTTP_METHOD /path"""

    conversation_history = [
        {"role": "system", "content": create_system_prompt_with_tools()},
        {"role": "user", "content": user_prompt}
    ]

    total_cost = 0.0

    try:
        for iteration in range(max_iterations):
            response = call_llm_with_tools(
                conversation_history,
                tools,
                temperature=0.0,
                max_tokens=500
                # include_reasoning uses OPENROUTER_INCLUDE_REASONING from .env
            )

            # Считаем стоимость
            usage = response.get("usage", {})
            total_cost += calculate_cost(usage, model)

            assistant_message = response["choices"][0]["message"]

            # Проверяем наличие tool_calls
            if "tool_calls" in assistant_message and assistant_message["tool_calls"]:
                # Выполняем tool calls
                tool_results = await execute_tool_calls(mcp_url, assistant_message["tool_calls"])

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

            # Получили финальный ответ
            final_content = assistant_message.get("content", "").strip()
            method, request = parse_llm_response(final_content)

            return {"type": method, "request": request}, total_cost

        # Если достигли максимального количества итераций
        return {"type": "GET", "request": "/v1/assets"}, total_cost

    except Exception as e:
        click.echo(f"⚠️  Ошибка при генерации для вопроса '{question[:50]}...': {e}", err=True)
        return {"type": "GET", "request": "/v1/assets"}, total_cost


def generate_api_call(question: str, examples: list[dict[str, str]], model: str) -> tuple[dict[str, str], float]:
    """Сгенерировать API запрос для вопроса (базовый режим без MCP)

    Returns:
        tuple: (result_dict, cost_in_dollars)
    """
    prompt = create_prompt(question, examples)

    messages = [{"role": "user", "content": prompt}]

    try:
        response = call_llm(messages, temperature=0.0, max_tokens=200)
        llm_answer = response["choices"][0]["message"]["content"].strip()

        method, request = parse_llm_response(llm_answer)

        # Рассчитываем стоимость
        usage = response.get("usage", {})
        cost = calculate_cost(usage, model)

        return {"type": method, "request": request}, cost

    except Exception as e:
        click.echo(f"⚠️  Ошибка при генерации для вопроса '{question[:50]}...': {e}", err=True)
        # Возвращаем fallback
        return {"type": "GET", "request": "/v1/assets"}, 0.0


async def load_mcp_tools(mcp_url: str) -> list[dict[str, Any]]:
    """Загрузить tools от MCP сервера"""
    async with MCPClient(base_url=mcp_url) as client:
        return await client.get_openai_tools()


@click.command()
@click.option(
    "--test-file",
    type=click.Path(exists=True, path_type=Path),
    default="data/processed/test.csv",
    help="Путь к test.csv",
)
@click.option(
    "--train-file",
    type=click.Path(exists=True, path_type=Path),
    default="data/processed/train.csv",
    help="Путь к train.csv",
)
@click.option(
    "--output-file",
    type=click.Path(path_type=Path),
    default="data/processed/submission.csv",
    help="Путь к submission.csv",
)
@click.option("--num-examples", type=int, default=10, help="Количество примеров для few-shot")
@click.option("--mcp-url", type=str, default="http://localhost:8765", help="URL MCP сервера")
@click.option("--use-mcp/--no-mcp", default=True, help="Использовать MCP tools")
@click.option("--max-iterations", type=int, default=3, help="Максимальное количество итераций tool calling")
def main(  # noqa: C901
    test_file: Path,
    train_file: Path,
    output_file: Path,
    num_examples: int,
    mcp_url: str,
    use_mcp: bool,
    max_iterations: int
) -> None:
    """Генерация submission.csv для хакатона с использованием MCP tools"""
    from src.app.core.config import get_settings

    click.echo("🚀 Генерация submission файла...")
    click.echo(f"📖 Загрузка примеров из {train_file}...")

    # Получаем настройки для определения модели
    settings = get_settings()
    model = settings.openrouter_model

    # Загружаем примеры для few-shot
    examples = load_train_examples(train_file, num_examples)
    click.echo(f"✅ Загружено {len(examples)} примеров для few-shot learning")
    click.echo(f"🤖 Используется модель: {model}")

    # Загружаем MCP tools если нужно
    tools = []
    if use_mcp:
        click.echo(f"🔄 Загрузка MCP tools с {mcp_url}...")
        try:
            tools = asyncio.run(load_mcp_tools(mcp_url))
            click.echo(f"✅ Загружено {len(tools)} MCP tools")
            click.echo(f"🔧 Максимум итераций tool calling: {max_iterations}")
        except Exception as e:
            click.echo(f"⚠️  Не удалось загрузить MCP tools: {e}")
            click.echo("   Переключаюсь на базовый режим без MCP")
            use_mcp = False

    # Читаем тестовый набор
    click.echo(f"📖 Чтение {test_file}...")
    test_questions = []
    with open(test_file, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            test_questions.append({"uid": row["uid"], "question": row["question"]})

    click.echo(f"✅ Найдено {len(test_questions)} вопросов для обработки")

    # Генерируем ответы
    mode_str = "MCP tools" if use_mcp else "базовый режим"
    click.echo(f"\n🤖 Генерация API запросов ({mode_str})...")
    results = []
    total_cost = 0.0

    # Используем tqdm с postfix для отображения стоимости
    progress_bar = tqdm(test_questions, desc="Обработка")

    for item in progress_bar:
        if use_mcp:
            # Асинхронная генерация с MCP tools
            api_call, cost = asyncio.run(
                generate_api_call_with_mcp(
                    item["question"],
                    examples,
                    tools,
                    mcp_url,
                    model,
                    max_iterations
                )
            )
        else:
            # Базовая генерация без MCP
            api_call, cost = generate_api_call(item["question"], examples, model)

        total_cost += cost
        results.append({"uid": item["uid"], "type": api_call["type"], "request": api_call["request"]})

        # Обновляем postfix с текущей стоимостью
        progress_bar.set_postfix({"cost": f"${total_cost:.4f}"})

    # Записываем в submission.csv
    click.echo(f"\n💾 Сохранение результатов в {output_file}...")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["uid", "type", "request"], delimiter=";")
        writer.writeheader()
        writer.writerows(results)

    click.echo(f"✅ Готово! Создано {len(results)} записей в {output_file}")
    click.echo(f"\n💰 Общая стоимость генерации: ${total_cost:.4f}")
    click.echo(f"   Средняя стоимость на запрос: ${total_cost / len(results):.6f}")
    click.echo("\n📊 Статистика по типам запросов:")
    type_counts: dict[str, int] = {}
    for r in results:
        type_counts[r["type"]] = type_counts.get(r["type"], 0) + 1
    for method, count in sorted(type_counts.items()):
        click.echo(f"  {method}: {count}")


if __name__ == "__main__":
    main()
