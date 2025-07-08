import asyncio
import json
import os
import tempfile
import traceback

from flask import Flask, request, jsonify, render_template
import ollama
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import speech_recognition as sr
import pydub

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/voice-to-text", methods=["POST"])
def voice_to_text():
    """
    Receives audio file from browser, converts it to WAV,
    then performs speech-to-text using Google's API.
    """
    try:
        if 'audio' not in request.files:
            return jsonify({"success": False, "error": "No audio file provided"}), 400
        
        audio_file = request.files['audio']
        
        if audio_file.filename == '':
            return jsonify({"success": False, "error": "No audio file selected"}), 400
        
        # Convert audio to WAV using pydub
        sound = pydub.AudioSegment.from_file(audio_file)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as wav_file:
            wav_filename = wav_file.name
        
        sound.export(wav_filename, format="wav")
        
        try:
            recognizer = sr.Recognizer()
            with sr.AudioFile(wav_filename) as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio_data = recognizer.record(source)
            
            text = recognizer.recognize_google(audio_data)
            
            return jsonify({"success": True, "text": text})
        
        finally:
            if os.path.exists(wav_filename):
                os.unlink(wav_filename)

    except Exception as e:
        print("--- AN UNHANDLED ERROR OCCURRED ---")
        traceback.print_exc()
        print("---------------------------------")
        return jsonify({
            "success": False,
            "error": "An unexpected server error occurred during audio processing."
        }), 500


@app.route("/chat", methods=["POST"])
def chat_endpoint():
    """
    Receives a prompt JSON, sends it to Ollama + MCP tools,
    returns the response or tool execution results.
    """
    data = request.get_json()
    if not data or "prompt" not in data:
        return jsonify({"error": "A 'prompt' is required in the JSON body."}), 400

    prompt = data["prompt"]
    result = asyncio.run(handle_chat_request(prompt))
    
    if result.get("status") == "error":
        return jsonify(result), 500
        
    return jsonify(result)


async def handle_chat_request(prompt: str):
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
        print(f"An error occurred during the chat request: {e}")
        traceback.print_exc()
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
