"""Text query endpoint."""

from fastapi import APIRouter, Depends

from src.api.errors import ErrorResponse
from src.api.schemas.rag import QueryRequest, RagResponse
from src.services.rag_service import RAGService, get_rag_service
from src.utils.timing import Timer

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
    with Timer() as timer:
        response = service.query(request.query)

    # total_ms is wall clock for the service call, never a sum of stage timings.
    response.latency.total_ms = round(timer.elapsed_ms, 3)
    return response
