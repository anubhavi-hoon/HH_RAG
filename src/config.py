"""Central runtime configuration for the HH_RAG service.

Every value that other modules would otherwise hard-code lives here, so adding a
language or changing an upload limit is a single-line edit.
"""

import os
from enum import Enum
from typing import List, Tuple

SERVICE_NAME = "hh-rag"
SERVICE_VERSION = "0.1.0"


class Language(str, Enum):
    """Language codes accepted by the API contract.

    Only `en` and `hi` are supported today. Adding `bn`, `ta`, `te`, `mr`, ...
    means adding members here — no other module enumerates the language set.
    """

    EN = "en"
    HI = "hi"


DEFAULT_LANGUAGE: Language = Language.EN
SUPPORTED_LANGUAGES: Tuple[str, ...] = tuple(language.value for language in Language)

MAX_AUDIO_BYTES: int = int(os.getenv("HH_RAG_MAX_AUDIO_BYTES", 10 * 1024 * 1024))
ALLOWED_AUDIO_CONTENT_TYPE_PREFIXES: Tuple[str, ...] = (
    "audio/",
    "video/webm",
    "application/octet-stream",
)

REQUEST_ID_HEADER = "X-Request-ID"
#: Full server-side request duration in ms, measured by RequestContextMiddleware.
PROCESS_TIME_HEADER = "X-Process-Time-Ms"

_DEFAULT_CORS_ORIGINS: Tuple[str, ...] = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
)


def cors_origins() -> List[str]:
    """Allowed browser origins, overridable via `HH_RAG_CORS_ORIGINS` (comma-separated)."""
    raw = os.getenv("HH_RAG_CORS_ORIGINS", "").strip()
    if not raw:
        return list(_DEFAULT_CORS_ORIGINS)
    return [origin.strip() for origin in raw.split(",") if origin.strip()]
