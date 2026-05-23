import asyncio
import json
import logging

import chromadb
from models.document import Chunk, SearchResult
from models.interfaces import BaseRepository

logger = logging.getLogger(__name__)


class ChromaRepository(BaseRepository):
    def __init__(self, collection: chromadb.Collection, lock: asyncio.Lock) -> None:
        self._col = collection
        self._lock = lock

    def upsert(self, chunks: list[Chunk], embeddings: list[list[float]]) -> int:
        if not chunks:
            return 0
        self._col.upsert(
            ids=[c.chunk_id for c in chunks],
            embeddings=embeddings,
            documents=[c.text for c in chunks],
            metadatas=[
                {
                    "url": c.url,
                    "chunk_index": c.chunk_index,
                    "total_chunks": c.total_chunks,
                    "char_count": c.char_count,
                    "extras": json.dumps(c.extras, ensure_ascii=False),
                    "ingested_at": c.ingested_at,
                }
                for c in chunks
            ],
        )
        return len(chunks)

    def query(
        self,
        vector: list[float],
        top_k: int,
        where: dict | None = None,
    ) -> list[SearchResult]:
        kwargs: dict = {"query_embeddings": [vector], "n_results": top_k, "include": ["documents", "metadatas", "distances"]}
        if where:
            kwargs["where"] = where

        result = self._col.query(**kwargs)
        if not result["ids"] or not result["ids"][0]:
            return []

        results: list[SearchResult] = []
        for chunk_id, doc, meta, dist in zip(
            result["ids"][0],
            result["documents"][0],
            result["metadatas"][0],
            result["distances"][0],
            strict=True,
        ):
            raw_extras = meta.get("extras", "{}")
            try:
                extras = json.loads(raw_extras)
            except (json.JSONDecodeError, TypeError):
                extras = {}

            results.append(
                SearchResult(
                    chunk_id=chunk_id,
                    url=meta.get("url", ""),
                    text=doc,
                    chunk_index=int(meta.get("chunk_index", 0)),
                    score=round(1.0 - float(dist), 4),
                    extras=extras,
                    char_count=int(meta.get("char_count", 0)),
                )
            )
        return results

    def collection_stats(self) -> dict:
        count = self._col.count()
        return {
            "collection": self._col.name,
            "total_chunks": count,
        }
