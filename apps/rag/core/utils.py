import hashlib
import re


def safe_name(url: str) -> str:
    """Convert a URL to a filesystem-safe slug (mirrors scraper's safe_name)."""
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", url)


def deterministic_chunk_id(url: str, chunk_index: int) -> str:
    """Stable 40-hex-char ID for a chunk — safe for ChromaDB upsert."""
    raw = f"{url}|{chunk_index}"
    return hashlib.sha256(raw.encode()).hexdigest()[:40]
