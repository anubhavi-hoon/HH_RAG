"""Uniform error contract.

Every failure leaves the API in the same shape, so the frontend can render it
without special-casing:

    {"error": {"code": "RETRIEVAL_FAILED", "message": "..."}}

Internal detail (stack traces, exception types) is logged server-side and never
sent to the client.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.services.rag_service import ErrorCode, RagServiceError

logger = logging.getLogger("hh_rag.api")


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    """Documented error shape shown in the OpenAPI schema."""

    error: ErrorBody


def error_payload(code: ErrorCode, message: str) -> Dict[str, Any]:
    return {"error": {"code": code.value, "message": message}}


def api_error(status_code: int, code: ErrorCode, message: str) -> HTTPException:
    """Raise-able HTTPException carrying an explicit error code."""
    return HTTPException(
        status_code=status_code,
        detail={"code": code.value, "message": message},
    )


def internal_error_response() -> JSONResponse:
    """Generic 500 body used when an unexpected exception escapes a route."""
    return JSONResponse(
        status_code=500,
        content=error_payload(
            ErrorCode.INTERNAL_ERROR, "An unexpected internal error occurred."
        ),
    )


def _default_code(status_code: int) -> ErrorCode:
    if status_code == 404:
        return ErrorCode.NOT_FOUND
    if status_code >= 500:
        return ErrorCode.INTERNAL_ERROR
    return ErrorCode.INVALID_QUERY


def _first_validation_message(exc: RequestValidationError) -> str:
    for error in exc.errors():
        message = str(error.get("msg", "")).strip()
        if message:
            return message.replace("Value error, ", "")
    return "Request payload failed validation."


def register_exception_handlers(app: FastAPI) -> None:
    """Attach handlers that render every failure as the error envelope."""

    @app.exception_handler(RagServiceError)
    async def _handle_service_error(_: Request, exc: RagServiceError) -> JSONResponse:
        logger.warning("rag service error: %s (%s)", exc.code.value, exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload(exc.code, exc.message),
        )

    # Starlette's base class also covers FastAPI's HTTPException and router 404/405s.
    @app.exception_handler(StarletteHTTPException)
    async def _handle_http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        detail: Any = exc.detail
        code: Optional[str] = None
        message: str

        if isinstance(detail, dict) and "code" in detail:
            code = str(detail["code"])
            message = str(detail.get("message", ""))
        else:
            message = str(detail)

        resolved = code or _default_code(exc.status_code).value
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": resolved, "message": message}},
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(RequestValidationError)
    async def _handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        code = (
            ErrorCode.AUDIO_INVALID
            if request.url.path.endswith("/voice")
            else ErrorCode.INVALID_QUERY
        )
        return JSONResponse(
            status_code=422,
            content=error_payload(code, _first_validation_message(exc)),
        )
