"""
HTTP routes for the Voice Kiosk app.

Kept intentionally thin: request/response handling only. All real work
happens in app.services.*
"""

import asyncio
import os
import tempfile
import traceback

from flask import Blueprint, current_app, jsonify, render_template, request
import pydub

from app.services.chat_service import handle_chat_request
from app.services.transcription import TranscriptionError, get_transcriber

bp = Blueprint("kiosk", __name__)


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/voice-to-text", methods=["POST"])
def voice_to_text():
    """Accepts an uploaded audio file, converts it to WAV, and transcribes
    it using whichever engine is configured (Whisper or Google)."""
    if "audio" not in request.files:
        return jsonify({"success": False, "error": "No audio file provided"}), 400

    audio_file = request.files["audio"]
    if audio_file.filename == "":
        return jsonify({"success": False, "error": "No audio file selected"}), 400

    wav_filename = None
    try:
        sound = pydub.AudioSegment.from_file(audio_file)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as wav_file:
            wav_filename = wav_file.name
        sound.export(wav_filename, format="wav")

        transcriber = get_transcriber(current_app.config["APP_CONFIG"])
        text = transcriber.transcribe(wav_filename)

        return jsonify({"success": True, "text": text})

    except TranscriptionError as exc:
        # Expected, recoverable case: audio came through fine but no speech
        # could be recognized in it. Not a server error.
        return jsonify({"success": False, "error": str(exc)}), 400

    except Exception:
        traceback.print_exc()
        return jsonify(
            {
                "success": False,
                "error": "An unexpected server error occurred during audio processing.",
            }
        ), 500

    finally:
        if wav_filename and os.path.exists(wav_filename):
            # TEMP DEBUG: keep a copy to inspect by ear. Remove this import
            # import shutil
            # shutil.copy(wav_filename, "debug_last_recording.wav")
            os.unlink(wav_filename)


@bp.route("/chat", methods=["POST"])
def chat_endpoint():
    """Accepts {"prompt": "..."} and routes it through Ollama + MCP tools."""
    data = request.get_json(silent=True)
    if not data or "prompt" not in data:
        return jsonify({"error": "A 'prompt' is required in the JSON body."}), 400

    app_config = current_app.config["APP_CONFIG"]
    result = asyncio.run(handle_chat_request(data["prompt"], app_config))

    status_code = 500 if result.get("status") == "error" else 200
    return jsonify(result), status_code