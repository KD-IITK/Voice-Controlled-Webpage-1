"""
Speech-to-text service.

Two engines are supported and selected via `Config.STT_ENGINE`:

- WhisperTranscriber: fully offline, uses openai-whisper.
- GoogleTranscriber:   online, uses SpeechRecognition + Google's free API.

Both engines expose the same `.transcribe(wav_path) -> str` interface, so
the rest of the app doesn't need to know which one is active.
"""

from abc import ABC, abstractmethod


class TranscriptionError(Exception):
    """Raised when audio was received and processed, but no usable text
    could be produced from it (silence, unclear speech, or a network issue
    for online engines). Callers should treat this as a 4xx, not a 5xx."""


class Transcriber(ABC):
    @abstractmethod
    def transcribe(self, wav_path: str) -> str:
        """Return the transcribed text for a WAV file on disk."""
        raise NotImplementedError


class WhisperTranscriber(Transcriber):
    """Offline transcription using openai-whisper. Loads the model once
    and reuses it for every request."""

    def __init__(self, model_size: str = "base"):
        import whisper  # imported lazily so the google-only path doesn't need torch

        self._model = whisper.load_model(model_size)

    def transcribe(self, wav_path: str) -> str:
        result = self._model.transcribe(wav_path, fp16=False)
        text = result["text"].strip()

        if not text:
            raise TranscriptionError(
                "Could not detect any speech in the audio. Speak clearly and "
                "make sure your microphone isn't muted."
            )

        return text


class GoogleTranscriber(Transcriber):
    """Online transcription using SpeechRecognition's Google Web Speech API
    wrapper. No API key required, but needs internet access."""

    def __init__(self):
        import speech_recognition as sr

        self._sr = sr
        self._recognizer = sr.Recognizer()

    def transcribe(self, wav_path: str) -> str:
        with self._sr.AudioFile(wav_path) as source:
            self._recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio_data = self._recognizer.record(source)

        try:
            return self._recognizer.recognize_google(audio_data).strip()
        except self._sr.UnknownValueError as exc:
            raise TranscriptionError(
                "Could not understand the audio. Speak clearly and make sure "
                "your microphone isn't muted, or check that ffmpeg is "
                "installed (pydub needs it to convert the recording)."
            ) from exc
        except self._sr.RequestError as exc:
            raise TranscriptionError(
                f"Could not reach the Google speech recognition service: {exc}"
            ) from exc


_transcriber_instance: Transcriber | None = None


def get_transcriber(config) -> Transcriber:
    """Return a lazily-created, cached transcriber based on config.STT_ENGINE."""
    global _transcriber_instance

    if _transcriber_instance is not None:
        return _transcriber_instance

    if config.STT_ENGINE == "whisper":
        _transcriber_instance = WhisperTranscriber(config.WHISPER_MODEL_SIZE)
    elif config.STT_ENGINE == "google":
        _transcriber_instance = GoogleTranscriber()
    else:
        raise ValueError(
            f"Unknown STT_ENGINE '{config.STT_ENGINE}'. Use 'whisper' or 'google'."
        )

    return _transcriber_instance