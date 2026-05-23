import logging
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import torch
import torch.nn.functional as F
from models.interfaces import BaseEmbedder
from transformers import AutoModel, AutoTokenizer

logger = logging.getLogger(__name__)


def _mean_pool(last_hidden_state: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
    mask = attention_mask.unsqueeze(-1).expand(last_hidden_state.size()).float()
    return torch.sum(last_hidden_state * mask, dim=1) / torch.clamp(mask.sum(dim=1), min=1e-9)


class DictaBertEmbedder(BaseEmbedder):
    def __init__(self, model_name: str, device: str, batch_size: int, executor: ThreadPoolExecutor) -> None:
        self._device = torch.device(device)
        self._batch_size = batch_size
        self._executor = executor
        logger.info("Loading embedding model %s on %s …", model_name, device)
        self._tokenizer = AutoTokenizer.from_pretrained(model_name)
        self._model = AutoModel.from_pretrained(model_name).to(self._device).eval()
        logger.info("Embedding model ready.")

    def _encode_sync(self, texts: list[str]) -> list[list[float]]:
        all_vecs: list[list[float]] = []
        for i in range(0, len(texts), self._batch_size):
            batch = texts[i : i + self._batch_size]
            encoded = self._tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt",
            ).to(self._device)
            with torch.no_grad():
                output = self._model(**encoded)
            pooled = _mean_pool(output.last_hidden_state, encoded["attention_mask"])
            normalized = F.normalize(pooled, p=2, dim=1)
            all_vecs.extend(normalized.cpu().numpy().tolist())
        return all_vecs

    # ── LangChain Embeddings interface ────────────────────────────────────────

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._encode_sync(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._encode_sync([text])[0]

    # ── Async wrappers (run blocking encode in executor) ──────────────────────

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        import asyncio
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, self._encode_sync, texts)

    async def aembed_query(self, text: str) -> list[float]:
        vecs = await self.aembed_documents([text])
        return vecs[0]

    def embed_numpy(self, texts: list[str]) -> list[np.ndarray]:
        return [np.array(v) for v in self._encode_sync(texts)]
