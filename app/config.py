import os

class Config:
    # --- Flask ---
    HOST = os.environ.get("HOST", "0.0.0.0")
    PORT = int(os.environ.get("PORT", 5000))
    DEBUG = os.environ.get("FLASK_DEBUG", "true").lower() == "true"

    # --- Speech-to-text ---
    # "whisper" -> local/offline transcription via openai-whisper
    # "google"  -> online transcription via SpeechRecognition
    STT_ENGINE = os.environ.get("STT_ENGINE", "whisper").lower()
    WHISPER_MODEL_SIZE = os.environ.get("WHISPER_MODEL_SIZE", "base")

    # --- LLM / Ollama ---
    OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:0.5b")
    KIOSK_SYSTEM_PROMPT = (
        "You are a food kiosk operator. Respond with what the user wants to do."
    )

    # --- MCP tool server ---
    # Command used to launch the MCP tool server as a subprocess.
    MCP_SERVER_COMMAND = os.environ.get("MCP_SERVER_COMMAND", "python")
    MCP_SERVER_ARGS = [os.environ.get("MCP_SERVER_SCRIPT", "app/mcp_tools/kiosk_server.py")]


def get_config() -> Config:
    return Config()