from abc import ABC, abstractmethod
from pathlib import Path

import numpy as np
from langchain_core.embeddings import Embeddings

from models.document import Chunk, RawDocument, SearchResult


class BaseLoader(ABC):
    @abstractmethod
    def load(self, file_path: Path) -> RawDocument: ...


class BasePreprocessor(ABC):
    @abstractmethod
    def clean(self, texts: list[str]) -> list[str]: ...


class BaseChunker(ABC):
    @abstractmethod
    def chunk(self, doc: RawDocument, cleaned: list[str]) -> list[Chunk]: ...


class BaseEmbedder(Embeddings, ABC):
    """Extends LangChain's Embeddings so DictaBertEmbedder plugs into SemanticChunker."""

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    @abstractmethod
    def embed_query(self, text: str) -> list[float]: ...

    def embed_numpy(self, texts: list[str]) -> list[np.ndarray]:
        return [np.array(v) for v in self.embed_documents(texts)]


class BaseRepository(ABC):
    @abstractmethod
    def upsert(self, chunks: list[Chunk], embeddings: list[list[float]]) -> int: ...

    @abstractmethod
    def query(
        self,
        vector: list[float],
        top_k: int,
        where: dict | None = None,
    ) -> list[SearchResult]: ...

    @abstractmethod
    def collection_stats(self) -> dict: ...
