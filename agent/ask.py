"""CLI: python -m agent.ask "which frameworks have the most stars?"  (--rebuild re-embeds)"""
import argparse

import duckdb

from agent import llm
from agent.index import VectorIndex
from agent.loop import ask
from agent.schema_docs import CHUNKS
from agent.tools import DB_PATH


def build_paper_index() -> VectorIndex:
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    rows = conn.execute(
        "select title, abstract, primary_category, paper_url from fct_papers"
    ).fetchall()
    conn.close()
    records = [
        {"text": f"{t}. {a}", "title": t, "category": c, "url": u} for t, a, c, u in rows
    ]
    return VectorIndex(records, llm.embed)


def load_indexes(rebuild: bool) -> tuple[VectorIndex, VectorIndex]:
    # The schema index is tiny, so rebuild it whenever schema_docs.py changed.
    schema_stale = not VectorIndex.exists("schema") or (
        VectorIndex.load("schema", llm.embed).records != CHUNKS
    )
    if rebuild or schema_stale:
        VectorIndex(CHUNKS, llm.embed).save("schema")
    if rebuild or not VectorIndex.exists("papers"):
        print("Embedding papers (one-off, a few minutes on CPU)...")
        build_paper_index().save("papers")
    return VectorIndex.load("schema", llm.embed), VectorIndex.load("papers", llm.embed)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("question")
    parser.add_argument("--rebuild", action="store_true")
    parser.add_argument("--track", action="store_true", help="log this question to MLflow")
    args = parser.parse_args()
    schema_index, paper_index = load_indexes(args.rebuild)
    if args.track:
        from agent.tracking import tracked_ask

        print(tracked_ask(args.question, schema_index, paper_index)["answer"])
    else:
        print(ask(args.question, schema_index, paper_index))
