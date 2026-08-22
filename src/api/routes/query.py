import logging
from fastapi import APIRouter, Depends

from src.api.errors import ErrorResponse
from src.api.schemas.rag import QueryRequest, RagResponse
from src.services.rag_service import RAGService, get_rag_service
from src.utils.timing import Timer

logger = logging.getLogger("hh_rag.api.query")
router = APIRouter()


@router.post(
    "/query",
    response_model=RagResponse,
    responses={422: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
def query(
    request: QueryRequest,
    service: RAGService = Depends(get_rag_service),
) -> RagResponse:
    logger.info("Received query request (query_len=%d, require_grounding=%s)", len(request.query), request.require_grounding)
    with Timer() as timer:
        response = service.query(request.query, require_grounding=request.require_grounding)

    # total_ms is wall clock for the service call, never a sum of stage timings.
    response.latency.total_ms = round(timer.elapsed_ms, 3)
    logger.info("Completed query request in %.2fms (grounded=%s, confidence=%.2f)", response.latency.total_ms, response.grounded, response.confidence)
    return response
