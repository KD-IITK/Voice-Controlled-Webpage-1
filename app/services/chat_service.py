"""
Orchestrates a single chat turn:

1. Spin up the MCP tool server as a subprocess and open a session.
2. Advertise its tools to Ollama in the format Ollama expects.
3. Ask the LLM what to do with the user's prompt.
4. If the LLM wants to call a tool, execute it via MCP and return the result.
   Otherwise, return the LLM's direct text response.
"""

import json
import traceback

import ollama
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def _mcp_tools_to_ollama_format(mcp_tools) -> list[dict]:
    ollama_tools = []
    for tool in mcp_tools:
        parameters = {}
        if getattr(tool, "inputSchema", None):
            parameters = (
                tool.inputSchema
                if isinstance(tool.inputSchema, dict)
                else tool.inputSchema.model_dump()
            )

        ollama_tools.append(
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": parameters,
                },
            }
        )
    return ollama_tools


async def handle_chat_request(prompt: str, config) -> dict:
    """Run one chat turn against Ollama + the MCP tool server.

    Returns a dict with a "status" key of "tool_executed", "direct_response",
    or "error".
    """
    server_params = StdioServerParameters(
        command=config.MCP_SERVER_COMMAND,
        args=config.MCP_SERVER_ARGS,
    )

    try:
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()

                tools_result = await session.list_tools()
                ollama_tools = _mcp_tools_to_ollama_format(tools_result.tools)

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
                    return {
                        "status": "direct_response",
                        "data": response["message"]["content"],
                    }

                tool_call_results = []
                for tool_call in tool_calls:
                    function_name = tool_call["function"]["name"]
                    function_args = tool_call["function"]["arguments"]

                    result = await session.call_tool(function_name, function_args)
                    tool_call_results.append(
                        {
                            "tool_name": function_name,
                            "arguments": function_args,
                            "result": json.loads(result.content[0].text),
                        }
                    )

                return {"status": "tool_executed", "data": tool_call_results}

    except Exception as exc:  # noqa: BLE001 - surfaced to the caller as JSON
        traceback.print_exc()
        return {"status": "error", "message": str(exc)}