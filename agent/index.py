import json
from pathlib import Path
from typing import Callable

import faiss
import numpy as np

INDEX_DIR = Path("data/agent")

Embedder = Callable[[list[str]], np.ndarray]


class VectorIndex:
    """A FAISS inner-product index over text records, with the records kept alongside."""

    def __init__(self, records: list[dict], embedder: Embedder, vectors: np.ndarray | None = None):
        self.records = records
        self.embedder = embedder
        if vectors is None:
            vectors = embedder([r["text"] for r in records])
        self.vectors = vectors
        self.index = faiss.IndexFlatIP(vectors.shape[1])
        self.index.add(vectors)

    def search(self, query: str, k: int = 3) -> list[dict]:
        k = min(k, len(self.records))
        scores, ids = self.index.search(self.embedder([query]), k)
        return [{**self.records[i], "score": float(s)} for s, i in zip(scores[0], ids[0])]

    def save(self, name: str) -> None:
        INDEX_DIR.mkdir(parents=True, exist_ok=True)
        np.save(INDEX_DIR / f"{name}.npy", self.vectors)
        (INDEX_DIR / f"{name}.json").write_text(json.dumps(self.records), encoding="utf-8")

    @classmethod
    def load(cls, name: str, embedder: Embedder) -> "VectorIndex":
        records = json.loads((INDEX_DIR / f"{name}.json").read_text(encoding="utf-8"))
        return cls(records, embedder, np.load(INDEX_DIR / f"{name}.npy"))

    @classmethod
    def exists(cls, name: str) -> bool:
        return (INDEX_DIR / f"{name}.npy").exists() and (INDEX_DIR / f"{name}.json").exists()
