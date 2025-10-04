#!/usr/bin/env python3
"""
Advanced CLI with MCP tools support

Usage:
    poetry run chat-cli-adv --query "What's SBER price?"
    poetry run chat-cli-adv  # interactive mode
    poetry run chat-cli-adv --show-tools
"""

import asyncio
import json
import sys
from typing import Any

import click

from src.app.core import MCPClient, call_llm_with_tools, get_settings


def create_system_prompt() -> str:
    """System prompt for AI assistant"""
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


async def load_mcp_tools(mcp_url: str) -> list[dict[str, Any]]:
    """Load tools from MCP server"""
    async with MCPClient(base_url=mcp_url) as client:
        return await client.get_openai_tools()


async def execute_tool_calls(
    mcp_url: str,
    tool_calls: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Execute tool calls via MCP client"""
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


async def process_single_query(
    query: str,
    tools: list[dict[str, Any]],
    mcp_url: str,
    verbose: bool = False
) -> str:
    """Process a single query with MCP tools"""
    conversation_history = [
        {"role": "system", "content": create_system_prompt()},
        {"role": "user", "content": query}
    ]

    max_iterations = 5
    for iteration in range(max_iterations):
        response = call_llm_with_tools(
            conversation_history,
            tools,
            temperature=0.3
        )

        assistant_message = response["choices"][0]["message"]

        # Check for tool calls
        if "tool_calls" in assistant_message and assistant_message["tool_calls"]:
            if verbose:
                tool_names = [tc["function"]["name"] for tc in assistant_message["tool_calls"]]
                click.echo(f"\n   🔧 Executing tools: {', '.join(tool_names)}")

            # Execute tools
            tool_results = await execute_tool_calls(mcp_url, assistant_message["tool_calls"])

            # Add to conversation
            conversation_history.append({
                "role": "assistant",
                "content": assistant_message.get("content") or "",
                "tool_calls": assistant_message["tool_calls"]
            })

            for result in tool_results:
                conversation_history.append(result)

            # Continue loop for final answer
            continue

        # Final answer
        final_content = assistant_message.get("content", "")
        return final_content

    return "⚠️ Достигнуто максимальное количество итераций"


@click.command()
@click.option("--query", "-q", default=None, help="Single query mode (non-interactive)")
@click.option("--mcp-url", default="http://localhost:8765", help="MCP server URL")
@click.option("--show-tools", is_flag=True, help="Show available MCP tools and exit")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output (show tool calls)")
def main(query: str | None, mcp_url: str, show_tools: bool, verbose: bool) -> None:  # noqa: C901
    """Advanced AI Trading Assistant CLI with MCP tools support"""
    settings = get_settings()

    # Load MCP tools
    if verbose:
        click.echo(f"🔄 Loading MCP tools from {mcp_url}...", nl=False)

    try:
        tools = asyncio.run(load_mcp_tools(mcp_url))
        if verbose:
            click.echo(f" ✅ {len(tools)} tools loaded")
    except Exception as e:
        click.echo(f"❌ Failed to load MCP tools: {e}", err=True)
        click.echo("\n💡 Make sure MCP server is running:")
        click.echo("   poetry run mcp-server")
        click.echo(f"   Or check MCP server URL: {mcp_url}")
        sys.exit(1)

    # Show tools mode
    if show_tools:
        click.echo("\n📋 Available MCP Tools:")
        click.echo("=" * 70)
        for tool in tools:
            func = tool["function"]
            click.echo(f"\n🔧 {func['name']}")
            click.echo(f"   {func.get('description', 'No description')}")
        click.echo("\n" + "=" * 70)
        return

    # Single query mode
    if query:
        if verbose:
            click.echo(f"\n👤 Query: {query}\n")

        click.echo("🤖 Assistant: ", nl=False)
        answer = asyncio.run(process_single_query(query, tools, mcp_url, verbose))
        click.echo(answer)
        return

    # Interactive mode
    click.echo("\n" + "=" * 70)
    click.echo("🤖 AI Trading Assistant (Advanced CLI with MCP Tools)")
    click.echo("=" * 70)
    click.echo(f"Model: {settings.openrouter_model}")
    click.echo(f"MCP Server: {mcp_url}")
    click.echo(f"Tools loaded: {len(tools)}")
    click.echo("\nCommands:")
    click.echo("  • Type your questions in Russian")
    click.echo("  • 'exit' or 'quit' - exit")
    click.echo("  • 'clear' - clear conversation history")
    click.echo("  • 'tools' - list available MCP tools")
    click.echo("=" * 70)

    conversation_history = [{"role": "system", "content": create_system_prompt()}]

    while True:
        try:
            # Get user input
            user_input = click.prompt("\n👤 You", type=str, prompt_suffix=": ")

            if user_input.lower() in ["exit", "quit", "выход"]:
                click.echo("\n👋 До свидания!")
                break

            if user_input.lower() in ["clear", "очистить"]:
                conversation_history = [{"role": "system", "content": create_system_prompt()}]
                click.echo("🔄 История очищена")
                continue

            if user_input.lower() == "tools":
                click.echo("\n📋 Available tools:")
                for tool in tools:
                    click.echo(f"  • {tool['function']['name']}")
                continue

            # Add user message to history
            conversation_history.append({"role": "user", "content": user_input})

            click.echo("🤖 Assistant: ", nl=False)

            # Process with MCP tools
            max_iterations = 5
            iteration = 0

            while iteration < max_iterations:
                iteration += 1

                # Call LLM with tools
                response = call_llm_with_tools(
                    conversation_history,
                    tools,
                    temperature=0.3
                )

                assistant_message = response["choices"][0]["message"]

                # Check for tool calls
                if "tool_calls" in assistant_message and assistant_message["tool_calls"]:
                    # Show tool execution
                    tool_names = [tc["function"]["name"] for tc in assistant_message["tool_calls"]]
                    if verbose:
                        click.echo(f"\n   🔧 Calling: {', '.join(tool_names)}")

                    # Execute tools
                    tool_results = asyncio.run(
                        execute_tool_calls(mcp_url, assistant_message["tool_calls"])
                    )

                    # Add to history
                    conversation_history.append({
                        "role": "assistant",
                        "content": assistant_message.get("content") or "",
                        "tool_calls": assistant_message["tool_calls"]
                    })

                    for result in tool_results:
                        conversation_history.append(result)

                    # Continue loop for final answer
                    continue

                # Final answer
                final_content = assistant_message.get("content", "")

                if final_content:
                    click.echo(final_content)

                    # Save to history
                    conversation_history.append({
                        "role": "assistant",
                        "content": final_content
                    })

                break

            if iteration >= max_iterations:
                click.echo("\n⚠️ Достигнуто максимальное количество итераций")

        except KeyboardInterrupt:
            click.echo("\n\n👋 До свидания!")
            sys.exit(0)
        except Exception as e:
            click.echo(f"\n❌ Ошибка: {e}", err=True)
            if verbose:
                import traceback
                traceback.print_exc()


if __name__ == "__main__":
    main()
