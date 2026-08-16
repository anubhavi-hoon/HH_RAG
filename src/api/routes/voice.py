"""Voice query endpoint.

Handles HTTP-level upload concerns only; transcription and answering belong to
the injected :class:`RAGService`.
"""

from fastapi import APIRouter, Depends, File, UploadFile, status

from src.api.errors import ErrorResponse, api_error
from src.api.schemas.rag import RagResponse
from src.config import ALLOWED_AUDIO_CONTENT_TYPE_PREFIXES, MAX_AUDIO_BYTES
from src.services.rag_service import (
    AudioInput,
    AudioInvalidError,
    ErrorCode,
    RAGService,
    get_rag_service,
)
from src.utils.timing import Timer

router = APIRouter()


@router.post(
    "/voice",
    response_model=RagResponse,
    responses={
        413: {"model": ErrorResponse},
        415: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
    },
)
async def voice(
    file: UploadFile = File(...),
    service: RAGService = Depends(get_rag_service),
) -> RagResponse:
    content_type = (file.content_type or "").lower()
    if not content_type.startswith(ALLOWED_AUDIO_CONTENT_TYPE_PREFIXES):
        raise api_error(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            ErrorCode.AUDIO_INVALID,
            f"Unsupported content type: {file.content_type!r}. Expected audio.",
        )

    # Read one byte past the limit so oversized uploads are detectable.
    audio_bytes = await file.read(MAX_AUDIO_BYTES + 1)
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise api_error(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            ErrorCode.AUDIO_INVALID,
            f"Audio file exceeds {MAX_AUDIO_BYTES} bytes.",
        )
    if not audio_bytes:
        raise AudioInvalidError("Uploaded audio file is empty.")

    with Timer() as timer:
        response = service.voice(
            AudioInput(
                filename=file.filename or "recording",
                content_type=content_type,
                data=audio_bytes,
            )
        )

    # Covers STT + answering; upload transfer time is client-side, not counted here.
    response.latency.total_ms = round(timer.elapsed_ms, 3)
    return response
