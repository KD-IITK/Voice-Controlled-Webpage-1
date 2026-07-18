"""
Standalone terminal harness for exercising the MCP tool server + Ollama
without going through the Flask app or the browser. Handy while iterating
on prompts or tool definitions.

Run with:
    python scripts/mcp_cli.py
"""

import asyncio
import json
import sys
from pathlib import Path

# Allow running this script directly without installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import ollama
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.config import get_config
from app.services.chat_service import _mcp_tools_to_ollama_format


async def main():
    config = get_config()
    server_params = StdioServerParameters(
        command=config.MCP_SERVER_COMMAND, args=config.MCP_SERVER_ARGS
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            tools_result = await session.list_tools()
            ollama_tools = _mcp_tools_to_ollama_format(tools_result.tools)

            print(f"Connected. {len(ollama_tools)} tool(s) available. Ctrl+C to quit.\n")

            while True:
                prompt = input("write prompt: ")
                response = ollama.chat(
                    model=config.OLLAMA_MODEL,
                    messages=[
                        {"role": "assistant", "content": config.KIOSK_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    tools=ollama_tools,
                )

                tool_calls = response["message"].get("tool_calls")
                if not tool_calls:
                    print("No tool calls. Response:", response["message"]["content"])
                    continue

                for tool_call in tool_calls:
                    function_name = tool_call["function"]["name"]
                    function_args = tool_call["function"]["arguments"]
                    if isinstance(function_args, str):
                        function_args = json.loads(function_args)

                    print(f"Executing tool: {function_name}")
                    print(f"Arguments: {function_args}")

                    try:
                        result = await session.call_tool(function_name, function_args)
                        print(result.content[0].text)
                    except Exception as exc:  # noqa: BLE001
                        print(f"Error executing tool {function_name}: {exc}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBye!")