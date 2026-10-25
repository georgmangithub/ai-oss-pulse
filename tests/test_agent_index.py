import numpy as np

from agent.index import VectorIndex


def fake_embedder(texts):
    """Deterministic stand-in: one dimension per keyword, so retrieval is predictable."""
    keywords = ["star", "paper", "language"]
    vecs = np.array(
        [[float(k in t.lower()) + 0.01 for k in keywords] for t in texts], dtype="float32"
    )
    return vecs / np.linalg.norm(vecs, axis=1, keepdims=True)


RECORDS = [
    {"id": "a", "text": "stars of repos"},
    {"id": "b", "text": "arxiv paper abstracts"},
    {"id": "c", "text": "programming language of a repo"},
]


def test_search_returns_closest_record():
    index = VectorIndex(RECORDS, fake_embedder)
    assert index.search("which paper?", k=1)[0]["id"] == "b"
    assert index.search("most stars", k=1)[0]["id"] == "a"


def test_save_and_load_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr("agent.index.INDEX_DIR", tmp_path)
    VectorIndex(RECORDS, fake_embedder).save("t")
    assert VectorIndex.exists("t")
    loaded = VectorIndex.load("t", fake_embedder)
    assert loaded.search("language", k=1)[0]["id"] == "c"
