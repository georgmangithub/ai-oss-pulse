"""The only module that talks to a model server, so the backend can be swapped."""
import numpy as np
import ollama

CHAT_MODEL = "qwen2.5:3b"
EMBED_MODEL = "nomic-embed-text"


def chat(messages: list[dict], tools: list[dict] | None = None) -> dict:
    """One chat turn; returns the assistant message (may contain tool_calls)."""
    response = ollama.chat(
        model=CHAT_MODEL, messages=messages, tools=tools, options={"temperature": 0}
    )
    return response["message"]


def embed(texts: list[str]) -> np.ndarray:
    """Embed texts into a float32 matrix, L2-normalised so inner product = cosine."""
    response = ollama.embed(model=EMBED_MODEL, input=texts)
    vectors = np.array(response["embeddings"], dtype="float32")
    return vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
