# main.py

import asyncio
import json
# Add render_template to serve the HTML page
from flask import Flask, request, jsonify, render_template
import ollama
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

app = Flask(__name__)

# This is the new route to serve your web page
@app.route("/")
def index():
    return render_template("index.html")

# This is your existing chat API endpoint (no changes needed here)
@app.route("/chat", methods=["POST"])
def chat_endpoint():
    data = request.get_json()
    if not data or "prompt" not in data:
        return jsonify({"error": "A 'prompt' is required in the JSON body."}), 400

    prompt = data["prompt"]
    result = asyncio.run(handle_chat_request(prompt))
    
    if result.get("status") == "error":
        return jsonify(result), 500
        
    return jsonify(result)

async def handle_chat_request(prompt: str):
    """
    Handles a single chat request by spinning up an MCP client,
    communicating with the LLM, and executing tool calls.
    """
    server_params = StdioServerParameters(
        command="python",
        args=["server.py"],
    )

    try:
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()

                tools_result = await session.list_tools()
                
                ollama_tools = []
                for tool in tools_result.tools:
                    parameters = {}
                    if hasattr(tool, 'inputSchema') and tool.inputSchema:
                        parameters = tool.inputSchema if isinstance(tool.inputSchema, dict) else tool.inputSchema.model_dump()
                    
                    ollama_tool = {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": parameters
                        }
                    }
                    ollama_tools.append(ollama_tool)

                response = ollama.chat(
                    model="llama3.2:latest",
                    messages=[
                        {"role": "assistant", "content": "You are a food kiosk operator. Respond with what the user wants to do."},
                        {"role": "user", "content": prompt}
                    ],
                    tools=ollama_tools,
                )

                if response['message'].get('tool_calls'):
                    tool_call_results = []
                    for tool_call in response['message']['tool_calls']:
                        function_name = tool_call['function']['name']
                        function_args = tool_call['function']['arguments']
                        result = await session.call_tool(function_name, function_args)
                        
                        tool_call_results.append({
                            "tool_name": function_name,
                            "arguments": function_args,
                            "result": json.loads(result.content[0].text)
                        })
                    return {"status": "tool_executed", "data": tool_call_results}
                else:
                    return {"status": "direct_response", "data": response['message']['content']}

    except Exception as e:
        print(f"An error occurred during the request: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
