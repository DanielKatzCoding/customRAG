import asyncio
import logging
from pathlib import Path

from models.document import Chunk, IngestJob, SearchResult
from models.interfaces import (
    BaseChunker,
    BaseEmbedder,
    BaseLoader,
    BasePreprocessor,
    BaseRepository,
)

logger = logging.getLogger(__name__)


class IngestFacade:
    def __init__(
        self,
        loader: BaseLoader,
        preprocessor: BasePreprocessor,
        chunker: BaseChunker,
        embedder: BaseEmbedder,
        repository: BaseRepository,
        executor,
    ) -> None:
        self._loader = loader
        self._preprocessor = preprocessor
        self._chunker = chunker
        self._embedder = embedder
        self._repository = repository
        self._executor = executor

    async def ingest_file(self, file_path: Path, job: IngestJob) -> int:
        loop = asyncio.get_running_loop()

        doc = await loop.run_in_executor(self._executor, self._loader.load, file_path)
        cleaned = self._preprocessor.clean(doc.content)

        chunks: list[Chunk] = await loop.run_in_executor(
            self._executor, self._chunker.chunk, doc, cleaned
        )
        if not chunks:
            logger.warning("No chunks produced from %s", file_path.name)
            return 0

        embed_texts = [c.embed_text for c in chunks]
        embeddings: list[list[float]] = await loop.run_in_executor(
            self._executor, self._embedder.embed_documents, embed_texts
        )

        n = await loop.run_in_executor(self._executor, self._repository.upsert, chunks, embeddings)
        logger.info("Ingested %d chunks from %s", n, doc.url)
        job.chunks_ingested += n
        return n


class SearchFacade:
    def __init__(
        self,
        preprocessor: BasePreprocessor,
        embedder: BaseEmbedder,
        repository: BaseRepository,
        executor,
        default_top_k: int = 5,
    ) -> None:
        self._preprocessor = preprocessor
        self._embedder = embedder
        self._repository = repository
        self._executor = executor
        self._default_top_k = default_top_k

    async def search(
        self,
        query: str,
        top_k: int | None = None,
        site_key: str | None = None,
    ) -> tuple[list[SearchResult], str]:
        loop = asyncio.get_running_loop()
        k = top_k if top_k is not None else self._default_top_k

        cleaned = self._preprocessor.clean([query])
        clean_query = cleaned[0] if cleaned else query

        vector: list[float] = await loop.run_in_executor(
            self._executor, self._embedder.embed_query, clean_query
        )

        where = None
        if site_key:
            # ChromaDB metadata filter — site_key stored as part of the URL hostname
            # For now filter is not applied (URL-based filtering requires post-filter)
            # This is a known v0.1 limitation; search always returns global results
            logger.debug("site_key filter requested but not applied in v0.1: %s", site_key)

        results: list[SearchResult] = await loop.run_in_executor(
            self._executor, self._repository.query, vector, k, where
        )
        return results, clean_query
