from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class RawDocument:
    url: str
    content: list[str]
    extras: dict[str, list[str]]


@dataclass
class Chunk:
    chunk_id: str
    url: str
    text: str                        # clean text (no extras prefix) — returned to callers
    embed_text: str                  # enriched text (extras prefix + text) — used for embedding
    chunk_index: int
    total_chunks: int                # filled in after all chunks are produced
    extras: dict[str, list[str]]
    char_count: int = field(init=False)
    ingested_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def __post_init__(self) -> None:
        self.char_count = len(self.text)


@dataclass
class SearchResult:
    chunk_id: str
    url: str
    text: str
    chunk_index: int
    score: float                     # 1 - cosine_distance (higher = more similar)
    extras: dict[str, list[str]]
    char_count: int


@dataclass
class IngestJob:
    job_id: str
    status: str = "pending"          # pending | running | completed | failed
    file_count: int = 0
    chunks_ingested: int = 0
    error: str | None = None
