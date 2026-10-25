"""The only module that talks to a model server, so the backend can be swapped."""
import time

import numpy as np
import ollama

CHAT_MODEL = "qwen2.5:3b"
EMBED_MODEL = "nomic-embed-text"
EMBED_BATCH = 32
MAX_EMBED_CHARS = 1500  # title + start of the abstract is enough to find a topic


def chat(messages: list[dict], tools: list[dict] | None = None) -> dict:
    """One chat turn; returns the assistant message (may contain tool_calls)."""
    response = ollama.chat(
        model=CHAT_MODEL, messages=messages, tools=tools, options={"temperature": 0}
    )
    return response["message"]


def _embed_with_retry(batch: list[str], attempts: int = 6) -> list:
    """Ollama on Windows occasionally fails a request with a socket-buffer error; wait and retry."""
    for attempt in range(1, attempts + 1):
        try:
            return ollama.embed(model=EMBED_MODEL, input=batch)["embeddings"]
        except ollama.ResponseError:
            if attempt == attempts:
                raise
            time.sleep(5 * attempt)


def embed(texts: list[str]) -> np.ndarray:
    """Embed texts into a float32 matrix, L2-normalised so inner product = cosine."""
    batches = []
    for start in range(0, len(texts), EMBED_BATCH):
        batch = [t[:MAX_EMBED_CHARS] for t in texts[start : start + EMBED_BATCH]]
        batches.extend(_embed_with_retry(batch))
        if len(texts) > EMBED_BATCH:
            print(f"  embedded {min(start + EMBED_BATCH, len(texts))}/{len(texts)}", flush=True)
    vectors = np.array(batches, dtype="float32")
    return vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
