# Voice Kiosk

A voice-controlled food kiosk assistant. Speak (or type) an order, it gets
transcribed to text, sent to a local LLM (via Ollama), and the LLM calls MCP
tools to manage a shopping cart (add / remove / replace items).

**Tested and supported on: Windows PC + Microsoft Edge.** See
[Known limitations](#known-limitations) below before trying other browsers
or devices.

## Project layout

```
voice-kiosk/
├── app/
│   ├── __init__.py            # Flask app factory
│   ├── config.py              # All settings, overridable via env vars
│   ├── routes.py              # HTTP routes (/, /voice-to-text, /chat)
│   ├── services/
│   │   ├── transcription.py   # Whisper / Google STT, chosen via config
│   │   └── chat_service.py    # Ollama + MCP orchestration
│   └── mcp_tools/
│       └── kiosk_server.py    # MCP tool server (cart operations)
├── static/voice-script.js     # Frontend recording + fetch logic
├── templates/index.html       # Single-page UI
├── scripts/mcp_cli.py         # Terminal harness for testing tools/prompts
├── run.py                     # App entry point
├── requirements.txt
└── .gitignore
```

## Requirements

- Python 3.10+
- [ffmpeg](https://www.gyan.dev/ffmpeg/builds/) installed and on your PATH
  (needed by `pydub` to convert recorded audio to WAV). Check with:
  ```bash
  ffmpeg -version
  ```
- [Ollama](https://ollama.com) installed and running locally

## Setup

```bash
python -m venv venv
venv\Scripts\activate            # source venv/bin/activate on macOS/Linux
pip install -r requirements.txt
```

Pull the model set in `app/config.py` (default `qwen2.5:0.5b`):

```bash
ollama pull qwen2.5:0.5b
```

## Running

```bash
python run.py
```

Open **`http://localhost:5000`** in **Edge**.

## Configuration

All settings live in `app/config.py` as class attributes with defaults —
edit the file directly to change something (no `.env` file is used):

```python
class Config:
    HOST = os.environ.get("HOST", "0.0.0.0")
    PORT = int(os.environ.get("PORT", 5000))
    ...
```

| Setting | Default | Notes |
|---|---|---|
| `HOST` | `0.0.0.0` | |
| `PORT` | `5000` | |
| `DEBUG` | `true` | |
| `STT_ENGINE` | `whisper` | `whisper` (offline) or `google` (needs internet) |
| `WHISPER_MODEL_SIZE` | `base` | `tiny`/`base`/`small`/`medium`/`large` — bigger is slower but more accurate |
| `OLLAMA_MODEL` | `qwen2.5:0.5b` | must be pulled via `ollama pull` first |
| `MCP_SERVER_COMMAND` / `MCP_SERVER_ARGS` | `python` / `app/mcp_tools/kiosk_server.py` | how the MCP tool server subprocess is launched |

Each also reads an environment variable of the same name if you'd rather
override at runtime than edit the file (e.g. `set STT_ENGINE=google` before
running) — but for day-to-day use, editing the default in `config.py` is
simplest.

### Switching speech-to-text engines

Change `STT_ENGINE` in `app/config.py`:

- `whisper` — fully offline, larger first-run download, model loads once
  at process start.
- `google` — needs internet access, no local model download, but can
  return `UnknownValueError` on quiet/unclear audio (this is expected —
  the app returns a `400` with a clear message rather than crashing).

## Testing tools without the browser

```bash
python scripts/mcp_cli.py
```

Type prompts and see which MCP tool gets called, without needing a browser
or microphone — useful when iterating on prompts or tool definitions.

## Known limitations

- **Chrome**: recording can intermittently fail to transcribe. Chrome's
  `MediaRecorder` encodes audio differently than Edge, and the current
  frontend always labels the recording as `audio/wav` regardless of the
  actual codec. Edge works reliably; Chrome is not actively supported right
  now.
- **Mobile browsers (Android/iOS)**: voice input will show "not supported."
  This isn't a real capability gap — browsers block microphone access
  (`getUserMedia`) on any page loaded over plain `http://` unless it's
  `localhost`. Accessing the app from a phone via your PC's local IP counts
  as insecure, so the mic API is unavailable. Not currently set up to run
  over HTTPS.
- Both of the above have known fixes if needed later (Chrome: send the
  recorder's real MIME type instead of hardcoding `audio/wav`; mobile:
  serve over HTTPS with a self-signed cert via `ssl_context='adhoc'`) —
  just not applied, since the app only needs to run on PC + Edge for now.

## Troubleshooting

**500 error on `/voice-to-text`, traceback mentions `UnknownValueError`**
Means Google's API received audio but couldn't recognize any speech in it.
Check:
1. `ffmpeg -version` works in the same terminal Flask runs in.
2. Your mic isn't muted / input volume isn't too low.
3. Try setting `STT_ENGINE = "whisper"` in `app/config.py` instead — it's
   more forgiving and removes any network dependency, which helps isolate
   whether it's an audio quality issue or a Google API issue.

**"Voice input not supported in this browser"**
See [Known limitations](#known-limitations) — almost always means you're on
Chrome (codec issue) or accessing over `http://` from a non-localhost
device (mobile).

**Ollama-related errors in `/chat`**
Make sure Ollama is running (`ollama serve` if it's not already running as
a background service) and that the model in `config.py` has been pulled and the `model supports tool calling`.