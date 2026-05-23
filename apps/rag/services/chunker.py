import logging

from core.utils import deterministic_chunk_id
from langchain_experimental.text_splitter import SemanticChunker
from langchain_text_splitters import TokenTextSplitter
from models.document import Chunk, RawDocument
from models.interfaces import BaseChunker, BaseEmbedder

logger = logging.getLogger(__name__)

_EXTRAS_PREFIX_TEMPLATE = "[תגיות: {tags}]\n"


def _build_extras_prefix(extras: dict[str, list[str]]) -> str:
    all_tags = [tag for tags in extras.values() for tag in tags]
    if not all_tags:
        return ""
    return _EXTRAS_PREFIX_TEMPLATE.format(tags=", ".join(all_tags))


class LangChainSemanticChunker(BaseChunker):
    def __init__(
        self,
        embedder: BaseEmbedder,
        breakpoint_threshold_type: str = "percentile",
        breakpoint_threshold_amount: int = 85,
        max_chars: int = 1200,
        token_size: int = 256,
    ) -> None:
        self._semantic_chunker = SemanticChunker(
            embeddings=embedder,
            breakpoint_threshold_type=breakpoint_threshold_type,
            breakpoint_threshold_amount=breakpoint_threshold_amount,
        )
        self._token_splitter = TokenTextSplitter(chunk_size=token_size, chunk_overlap=20)
        self._max_chars = max_chars

    def chunk(self, doc: RawDocument, cleaned: list[str]) -> list[Chunk]:
        if not cleaned:
            logger.warning("No content to chunk for %s", doc.url)
            return []

        extras_prefix = _build_extras_prefix(doc.extras)
        full_text = "\n".join(cleaned)
        enriched_text = extras_prefix + full_text if extras_prefix else full_text

        raw_chunks = self._semantic_chunker.split_text(enriched_text)

        # Fallback: split oversized chunks by token count
        final_texts: list[str] = []
        for chunk_text in raw_chunks:
            if len(chunk_text) > self._max_chars:
                final_texts.extend(self._token_splitter.split_text(chunk_text))
            else:
                final_texts.append(chunk_text)

        chunks: list[Chunk] = []
        for i, text in enumerate(final_texts):
            # Strip extras prefix from the display text if it's at the start
            display_text = text
            if extras_prefix and display_text.startswith(extras_prefix):
                display_text = display_text[len(extras_prefix):]

            chunks.append(
                Chunk(
                    chunk_id=deterministic_chunk_id(doc.url, i),
                    url=doc.url,
                    text=display_text.strip(),
                    embed_text=text,         # keep full enriched text for embedding
                    chunk_index=i,
                    total_chunks=len(final_texts),
                    extras=doc.extras,
                )
            )

        logger.debug("Produced %d chunks from %s", len(chunks), doc.url)
        return chunks
