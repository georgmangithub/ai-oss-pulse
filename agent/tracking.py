"""MLflow tracking for the agent. Runs are stored locally under data/mlflow (git-ignored)."""
import hashlib
import json
import time
from pathlib import Path

import mlflow

from agent import llm
from agent.index import VectorIndex
from agent.loop import SYSTEM_PROMPT, ask
from agent.schema_docs import CHUNKS

MLFLOW_DIR = Path("data/mlflow")
EXPERIMENT = "ai-oss-pulse-agent"


def setup() -> None:
    MLFLOW_DIR.mkdir(parents=True, exist_ok=True)
    mlflow.set_tracking_uri(f"sqlite:///{(MLFLOW_DIR / 'mlflow.db').as_posix()}")
    if mlflow.get_experiment_by_name(EXPERIMENT) is None:
        mlflow.create_experiment(
            EXPERIMENT, artifact_location=(MLFLOW_DIR / "artifacts").resolve().as_uri()
        )
    mlflow.set_experiment(EXPERIMENT)


def config_params() -> dict:
    """What defines an agent 'version': models plus a hash of the prompt and schema docs."""
    fingerprint = SYSTEM_PROMPT + json.dumps(CHUNKS, sort_keys=True)
    return {
        "chat_model": llm.CHAT_MODEL,
        "embed_model": llm.EMBED_MODEL,
        "prompt_hash": hashlib.sha1(fingerprint.encode()).hexdigest()[:8],
    }


def run_question(
    question: str, schema_index: VectorIndex, paper_index: VectorIndex | None
) -> dict:
    """Ask once and collect everything worth logging."""
    trace: list = []
    start = time.time()
    answer = ask(question, schema_index, paper_index, trace=trace)
    sql_calls = [t for t in trace if t["tool"] == "run_sql"]
    return {
        "question": question,
        "answer": answer,
        "trace": trace,
        "latency_s": round(time.time() - start, 1),
        "steps": len(trace),
        "sql_calls": len(sql_calls),
        "sql_errors": sum(1 for t in sql_calls if "error" in t["result"]),
    }


def tracked_ask(
    question: str, schema_index: VectorIndex, paper_index: VectorIndex | None
) -> dict:
    """run_question, logged as one MLflow run."""
    setup()
    with mlflow.start_run(run_name=question[:60]):
        mlflow.log_params(config_params())
        mlflow.log_param("question", question[:250])
        result = run_question(question, schema_index, paper_index)
        mlflow.log_metrics(
            {k: result[k] for k in ("latency_s", "steps", "sql_calls", "sql_errors")}
        )
        mlflow.log_dict(
            {"answer": result["answer"], "trace": result["trace"]}, "interaction.json"
        )
    return result
