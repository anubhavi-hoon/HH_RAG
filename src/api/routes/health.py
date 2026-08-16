"""Liveness endpoint."""

from fastapi import APIRouter

from src.api.schemas.rag import HealthResponse
from src.config import SERVICE_NAME, SERVICE_VERSION

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Cheap liveness probe: no retrieval, model, or network work."""
    return HealthResponse(
        status="ok",
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
    )
