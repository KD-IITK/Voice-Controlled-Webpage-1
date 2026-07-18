"""
Entry point. Run with:

    python run.py

Configuration (which STT engine, which Ollama model, host/port, etc.) is
controlled via environment variables
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    config = app.config["APP_CONFIG"]
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)