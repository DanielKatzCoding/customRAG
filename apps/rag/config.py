from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).parent.parent.parent


class RagSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="RAG_",
        env_file=_REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str
    port: int
    log_level: str

    # ChromaDB
    chroma_path: str
    collection_name: str

    # Scraper output directory (relative to apps/rag/)
    output_dir: str

    # Embedding model
    embedding_model: str
    embedding_device: str
    embedding_batch_size: int

    # Chunking
    chunk_threshold_percentile: int
    chunk_max_chars: int
    chunk_token_size: int

    # Search
    search_default_top_k: int
