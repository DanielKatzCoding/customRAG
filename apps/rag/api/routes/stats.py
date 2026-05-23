import logging

from fastapi import APIRouter, Request

from api.schemas import HealthResponse, StatsResponse

router = APIRouter(tags=["stats"])
logger = logging.getLogger(__name__)


@router.get("/stats", response_model=StatsResponse)
async def stats(request: Request) -> StatsResponse:
    repo = request.app.state.repository
    col_stats = repo.collection_stats()
    settings = request.app.state.settings
    return StatsResponse(
        collection=col_stats["collection"],
        total_chunks=col_stats["total_chunks"],
        embedding_model=settings.embedding_model,
        chroma_path=settings.chroma_path,
    )


@router.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    try:
        request.app.state.repository.collection_stats()
        chroma_status = "connected"
    except Exception:
        logger.exception("ChromaDB health check failed")
        chroma_status = "error"

    model_loaded = getattr(request.app.state, "model_loaded", False)
    return HealthResponse(
        status="ok",
        chroma=chroma_status,
        model="loaded" if model_loaded else "not_loaded",
    )
