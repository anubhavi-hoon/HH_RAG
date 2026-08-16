"""Request correlation and request-duration measurement.

Every request gets an ``X-Request-ID`` (reused from the client when supplied) that
is echoed on the response and included in the access log line, so a frontend
request, a backend log entry and a benchmark record can be tied together.

The middleware also owns the *only* measurement of full server-side request
duration - routing, validation, the service call and response construction. It is
reported as the ``X-Process-Time-Ms`` header and in the log line. This is a
superset of the ``total_ms`` in the response body, which covers the service call
alone; the two are complementary, not competing definitions.
"""

import logging
import uuid
from contextvars import ContextVar
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from src.api.errors import internal_error_response
from src.config import PROCESS_TIME_HEADER, REQUEST_ID_HEADER
from src.utils.timing import Timer

logger = logging.getLogger("hh_rag.api")

_request_id: ContextVar[str] = ContextVar("request_id", default="-")


def current_request_id() -> str:
    """Request ID of the request being handled, or ``-`` outside a request."""
    return _request_id.get()


def _clean(value: Optional[str]) -> Optional[str]:
    # Client-supplied IDs are echoed into logs and headers, so keep them short and plain.
    if not value:
        return None
    candidate = value.strip()[:64]
    return candidate if candidate.isascii() and candidate.isprintable() else None


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Assign a request ID, measure request duration, and expose both to the client."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = _clean(request.headers.get(REQUEST_ID_HEADER)) or uuid.uuid4().hex
        token = _request_id.set(request_id)
        request.state.request_id = request_id

        timer = Timer().start()
        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "%s unhandled error on %s %s",
                request_id,
                request.method,
                request.url.path,
            )
            response = internal_error_response()
        finally:
            _request_id.reset(token)

        elapsed_ms = timer.stop()
        response.headers[REQUEST_ID_HEADER] = request_id
        response.headers[PROCESS_TIME_HEADER] = f"{elapsed_ms:.3f}"
        logger.info(
            "%s %s %s -> %s in %.2fms",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response
