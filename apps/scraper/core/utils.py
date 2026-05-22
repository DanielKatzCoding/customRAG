import hashlib
import re

_SAFE_CHARS = re.compile(r"[^\w\-]")
_MAX_SLUG_LEN = 120


def safe_name(url: str) -> str:
    """Return a filesystem-safe filename stem derived from *url*."""
    slug = _SAFE_CHARS.sub("_", url).strip("_. ")
    if len(slug) > _MAX_SLUG_LEN:
        digest = hashlib.sha256(url.encode()).hexdigest()[:12]
        slug = f"{slug[:_MAX_SLUG_LEN]}_{digest}"
    return slug or hashlib.sha256(url.encode()).hexdigest()
