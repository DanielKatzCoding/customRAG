from pydantic import BaseModel, Field

# ── Ingest ────────────────────────────────────────────────────────────────────

class IngestByPathsRequest(BaseModel):
    file_paths: list[str] = Field(..., min_length=1, max_length=100)


class IngestByUrlsRequest(BaseModel):
    urls: list[str] = Field(..., min_length=1, max_length=100)


class IngestResponse(BaseModel):
    job_id: str
    message: str
    file_count: int


class IngestStatusResponse(BaseModel):
    job_id: str
    status: str
    file_count: int
    chunks_ingested: int
    error: str | None = None


# ── Search ────────────────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=50)
    site_key: str | None = None


class SearchResultItem(BaseModel):
    chunk_id: str
    url: str
    text: str
    chunk_index: int
    score: float
    extras: dict[str, list[str]]
    char_count: int


class SearchResponse(BaseModel):
    results: list[SearchResultItem]
    query_clean: str
    total: int


# ── Stats ─────────────────────────────────────────────────────────────────────

class StatsResponse(BaseModel):
    collection: str
    total_chunks: int
    embedding_model: str
    chroma_path: str


class HealthResponse(BaseModel):
    status: str
    chroma: str
    model: str
