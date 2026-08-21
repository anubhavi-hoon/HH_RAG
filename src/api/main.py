"""FastAPI application entrypoint.

Run locally with:
    uvicorn src.api.main:app --reload
"""

import logging
import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.errors import register_exception_handlers
from src.api.middleware import RequestContextMiddleware
from src.api.routes import health, query, voice
from src.config import (
    PROCESS_TIME_HEADER,
    REQUEST_ID_HEADER,
    SERVICE_VERSION,
    cors_origins,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
_log = logging.getLogger("hh_rag.main")
_log.info("Starting HH_RAG service. SARVAM_API_KEY configured: %s", bool(os.getenv("SARVAM_API_KEY")))


app = FastAPI(
    title="HH_RAG API",
    description="Voice-enabled multilingual RAG API (mock service layer).",
    version=SERVICE_VERSION,
)

app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=[REQUEST_ID_HEADER, PROCESS_TIME_HEADER],
)

register_exception_handlers(app)

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(query.router, prefix="/api", tags=["rag"])
app.include_router(voice.router, prefix="/api", tags=["rag"])
