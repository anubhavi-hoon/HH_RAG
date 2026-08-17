"""
Sarvam AI Speech-to-Text Service.
Project: HH Goa 2026 Voice-Enabled Multilingual RAG System.

Provides high-performance, accurate transcription for Indian languages and English
using the official Sarvam AI API (saaras:v3 model).
"""

import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Optional

from src.services.rag_service import AudioInvalidError, SttFailedError

logger = logging.getLogger("sarvam_stt")

DEFAULT_SARVAM_MODEL = "saaras:v3"
DEFAULT_SARVAM_MODE = "transcribe"
DEFAULT_LANGUAGE_CODE = "unknown"


@dataclass(frozen=True)
class STTResult:
    """Internal result object for speech-to-text transcriptions."""

    transcript: str
    language_code: Optional[str] = None
    latency_ms: float = 0.0
    request_id: Optional[str] = None


class SarvamSTTService:
    """
    Dedicated Speech-to-Text service utilizing Sarvam AI API.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        client: Optional[Any] = None,
        model: str = DEFAULT_SARVAM_MODEL,
        mode: str = DEFAULT_SARVAM_MODE,
        language_code: str = DEFAULT_LANGUAGE_CODE,
    ) -> None:
        """
        Initializes the Sarvam STT service with dependency injection support.

        Args:
            api_key: Optional Sarvam API subscription key override.
            client: Optional pre-configured SarvamAI client instance (useful for mocking).
            model: Sarvam STT model name (default: saaras:v3).
            mode: Mode of transcription (default: transcribe).
            language_code: Target BCP-47 language code or 'unknown' for auto-detection.
        """
        self._api_key = api_key
        self._client = client
        self.model = model
        self.mode = mode
        self.language_code = language_code

    def _get_client(self) -> Any:
        """Lazily initialize and return the SarvamAI client."""
        if self._client is not None:
            return self._client

        key = self._api_key or os.environ.get("SARVAM_API_KEY")
        if not key or not key.strip():
            raise SttFailedError(
                "SARVAM_API_KEY is not configured. Please set the environment variable or specify it in .env."
            )

        try:
            from sarvamai import SarvamAI

            self._client = SarvamAI(api_subscription_key=key.strip())
            return self._client
        except Exception as e:
            # Never expose keys in error details
            logger.error("Failed to initialize SarvamAI client")
            raise SttFailedError("Failed to initialize Sarvam STT client.") from e

    def transcribe(
        self,
        filename: str,
        content_type: str,
        audio_bytes: bytes,
    ) -> STTResult:
        """
        Transcribes audio bytes using Sarvam AI STT API and measures latency.

        Args:
            filename: Original audio filename (e.g. 'recording.webm').
            content_type: MIME type of the audio (e.g. 'audio/webm').
            audio_bytes: Raw binary audio payload.

        Returns:
            STTResult containing transcript, detected language code, and measured latency.

        Raises:
            AudioInvalidError: If the provided audio payload is empty.
            SttFailedError: If transcription fails due to API errors, timeouts, or empty output.
        """
        if not audio_bytes or len(audio_bytes) == 0:
            raise AudioInvalidError("Uploaded audio file is empty.")

        client = self._get_client()

        safe_filename = filename or "recording.webm"
        if "." not in safe_filename:
            safe_filename = f"{safe_filename}.webm"

        safe_content_type = (content_type or "audio/webm").split(";")[0].strip()

        # Prepare multipart file tuple
        file_payload = (safe_filename, audio_bytes, safe_content_type)

        t_start = time.perf_counter()
        try:
            response = client.speech_to_text.transcribe(
                file=file_payload,
                model=self.model,
                mode=self.mode,
                language_code=self.language_code,
            )
        except Exception as e:
            t_elapsed_ms = (time.perf_counter() - t_start) * 1000.0
            error_type = type(e).__name__
            logger.error(
                "Sarvam STT request failed after %.2f ms with error type %s",
                t_elapsed_ms,
                error_type,
            )
            raise SttFailedError(f"Speech-to-text transcription failed: {error_type}") from e

        t_end = time.perf_counter()
        latency_ms = (t_end - t_start) * 1000.0

        if response is None:
            raise SttFailedError("Speech-to-text returned an empty response.")

        raw_transcript = getattr(response, "transcript", None)
        if raw_transcript is None or not str(raw_transcript).strip():
            raise SttFailedError("Speech-to-text produced an empty transcript.")

        clean_transcript = str(raw_transcript).strip()
        detected_language = getattr(response, "language_code", None)
        req_id = getattr(response, "request_id", None)

        return STTResult(
            transcript=clean_transcript,
            language_code=detected_language,
            latency_ms=round(latency_ms, 3),
            request_id=req_id,
        )
