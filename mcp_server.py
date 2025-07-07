import asyncio
import ollama
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    # Define server parameters
    server_params = StdioServerParameters(
        command="python",  # The command to run your server
        args=["server.py"],  # Arguments to the command
    )

    # Connect to the server
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            # Initialize the connection
            await session.initialize()

            # List available tools
            tools_result = await session.list_tools()
            TOOLS = tools_result.tools
        
            # Convert MCP tools to Ollama format
            ollama_tools = []
            for tool in TOOLS:
                parameters = {}
                if hasattr(tool, 'inputSchema') and tool.inputSchema:
                    if isinstance(tool.inputSchema, dict):
                        parameters = tool.inputSchema
                    else:
                        parameters = tool.inputSchema.model_dump() if hasattr(tool.inputSchema, 'model_dump') else {}
                
                ollama_tool = {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": parameters
                    }
                }
                ollama_tools.append(ollama_tool)
            
            while(True):
                prompt = input("write prompt: ")
                response = ollama.chat(
                    model="llama3.2:latest",
                    messages=[{"role" : "assistant", "content" : "You are a food kiosk operator. Respond with what the user wants to do."},{"role": "user", "content": prompt}],
                    tools=ollama_tools,
                )
                
                # Handle tool calls and execute them
                if hasattr(response, 'message') and hasattr(response.message, 'tool_calls') and response.message.tool_calls:
                    # print("Tool calls detected:", response.message.tool_calls,"\n")
                    
                    # Execute each tool call
                    tool_results = []
                    for tool_call in response.message.tool_calls:
                        function_name = tool_call['function']['name']
                        function_args = tool_call['function']['arguments']
                        
                        print(f"Executing tool: {function_name}")
                        print(f"Arguments: {function_args}")
                        
                        try:
                            # Parse arguments if they're a string
                            if isinstance(function_args, str):
                                function_args = json.loads(function_args)
                            
                            # Execute the MCP tool
                            result = await session.call_tool(function_name, function_args)
                            
                            print(f"{result.content[0].text}")
                            # print(result[0])
                            tool_results.append({
                                "tool_call_id": tool_call.get('id', ''),
                                "role": "tool",
                                "name": function_name,
                                "content": str(result.content) if hasattr(result, 'content') else str(result)
                            })
                            
                        except Exception as e:
                            print(f"Error executing tool {function_name}: {e}")
                            tool_results.append({
                                "tool_call_id": tool_call.get('id', ''),
                                "role": "tool",
                                "name": function_name,
                                "content": f"Error: {str(e)}"
                            })              
                else:
                    print("No tool calls. Response:", response.message.content)

if __name__ == "__main__":
    asyncio.run(main())
