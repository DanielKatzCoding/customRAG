import logging
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path

import chromadb
from config import RagSettings
from core.logging_setup import setup_logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from services.chunker import LangChainSemanticChunker
from services.embedder import DictaBertEmbedder
from services.facade import IngestFacade, SearchFacade
from services.loader import JsonLoader
from services.preprocessor import HebrewPreprocessor
from services.repository import ChromaRepository

from api.routes import ingest, search, stats

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: RagSettings = app.state.settings
    setup_logging(settings.log_level)

    # Ensure directories exist
    chroma_path = Path(settings.chroma_path)
    output_dir = Path(settings.output_dir)
    chroma_path.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Single-worker executor: DictaBERT is not thread-safe for concurrent inference
    executor = ThreadPoolExecutor(max_workers=1)

    # Load embedding model (blocks until downloaded + loaded)
    embedder = DictaBertEmbedder(
        model_name=settings.embedding_model,
        device=settings.embedding_device,
        batch_size=settings.embedding_batch_size,
        executor=executor,
    )
    app.state.model_loaded = True

    # ChromaDB persistent client
    chroma_client = chromadb.PersistentClient(path=str(chroma_path))
    collection = chroma_client.get_or_create_collection(
        name=settings.collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    import asyncio
    lock = asyncio.Lock()
    repository = ChromaRepository(collection=collection, lock=lock)

    loader = JsonLoader()
    preprocessor = HebrewPreprocessor()
    chunker = LangChainSemanticChunker(
        embedder=embedder,
        breakpoint_threshold_type="percentile",
        breakpoint_threshold_amount=settings.chunk_threshold_percentile,
        max_chars=settings.chunk_max_chars,
        token_size=settings.chunk_token_size,
    )

    app.state.repository = repository
    app.state.ingest_facade = IngestFacade(
        loader=loader,
        preprocessor=preprocessor,
        chunker=chunker,
        embedder=embedder,
        repository=repository,
        executor=executor,
    )
    app.state.search_facade = SearchFacade(
        preprocessor=preprocessor,
        embedder=embedder,
        repository=repository,
        executor=executor,
        default_top_k=settings.search_default_top_k,
    )
    app.state.jobs: dict = {}
    app.state.ingest_running: dict = {"active": False}

    logger.info("RAG service ready on port %d", settings.port)
    yield

    executor.shutdown(wait=True)
    logger.info("RAG service shut down.")


def create_app() -> FastAPI:
    settings = RagSettings()

    app = FastAPI(
        title="Hebrew RAG Service",
        version="0.1.0",
        description="Semantic search over Hebrew scraped content via DictaBERT + ChromaDB",
        lifespan=lifespan,
    )
    app.state.settings = settings

    @app.exception_handler(ValueError)
    async def value_error_handler(_request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, _exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error on %s %s", request.method, request.url)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    app.include_router(ingest.router)
    app.include_router(search.router)
    app.include_router(stats.router)

    return app


app = create_app()
