# ai-oss-pulse

A small, free, fully local data platform that tracks the AI open-source ecosystem (GitHub repos and
arXiv papers) and lets you ask questions about it in plain English.

It is a learning project built end to end: ingestion, a Delta Lake bronze layer, dbt models on
DuckDB, Airflow orchestration, a retrieval-grounded NL-to-SQL agent running on a local model,
and MLflow-tracked evaluation. Everything runs on a laptop with no paid services.

## Architecture

```
GitHub API ──┐                                   ┌─> dbt (DuckDB) ──> marts ──┐
             ├─> raw files ─> bronze Delta ──────┤                            ├─> NL-to-SQL agent ──> MLflow
arXiv API  ──┘   (data/raw)   (delta-rs)         └─> orchestrated by Airflow  │   (FAISS + Ollama)     (eval)
                                                                              └─ paper search (FAISS)
```

| Layer | Folder | What it does |
|---|---|---|
| Ingestion | `ingestion/` | Pulls GitHub repos (4 topics) and recent arXiv papers into dated raw files, then writes typed, partitioned Delta tables (`data/lakehouse/bronze`). |
| Transformation | `transform/` | dbt project on DuckDB: staging (typing, cleaning) → intermediate (star changes over 1/7/30 days) → marts (`dim_repo`, `fct_repo_daily`, `fct_papers`, `mart_framework_momentum`). 19 dbt tests. |
| Orchestration | `orchestration/` | Airflow in Docker Compose. Daily DAG: GitHub + arXiv ingestion in parallel → bronze → `dbt build`, with retries. |
| Agent | `agent/` | Answers questions with tool calling: a read-only SQL tool and a paper search tool, grounded by FAISS retrieval of schema docs and example queries. Runs on Ollama. |
| Evaluation | `agent/eval/` | 13 scored questions, logged to MLflow. |

## Run it

Requirements: Python 3.13, [Ollama](https://ollama.com), Docker Desktop (only for Airflow).

```bash
python -m venv .venv && .venv/Scripts/activate
pip install -r requirements.txt -r requirements-eval.txt
echo GITHUB_TOKEN=your_token > .env      # a GitHub token raises API rate limits

python -m ingestion.github               # raw GitHub snapshot
python -m ingestion.arxiv                # raw arXiv papers
python -m ingestion.to_delta             # raw -> bronze Delta tables
cd transform && dbt build --profiles-dir . && cd ..   # bronze -> marts + tests
```

Ask the agent (first run embeds ~1,900 papers, a few minutes on CPU):

```bash
ollama pull qwen2.5:3b
ollama pull nomic-embed-text
python -m agent.ask "which frameworks have the most stars?"
```

Run the evaluation and browse results:

```bash
python -m agent.eval
mlflow ui --backend-store-uri sqlite:///data/mlflow/mlflow.db   # http://localhost:5000
```

Run the pipeline daily with Airflow:

```bash
cd orchestration && docker compose up -d --build     # UI at http://localhost:8080
```

## Evaluation

`python -m agent.eval` asks 13 questions and scores them automatically: numeric answers are checked
against a trusted reference SQL query, paper questions must call the search tool, and unsafe or
off-topic requests must be refused.

Latest result (`qwen2.5:3b`, CPU only): **13/13 (100%)**, average about 15 seconds per question.

Caveat: this is a development set. The first run scored 11/13; I then fixed a scorer bug (it did not
accept "Ten" for 10), added a prompt rule about sort order and a column note, and tightened one
reference query. The questions were not held out, so 100% overstates real-world accuracy. A fair
next step is a separate held-out set of questions the prompt was never tuned on.

Every run logs the model names, a hash of the prompt and schema docs, per-question latency, SQL
error rate and the full tool-call trace, so a prompt change can be compared against the previous run.

## Design decisions

- **Layers talk only through tables.** Ingestion writes Delta, dbt reads Delta, the agent reads only
  the marts. Each piece can be swapped on its own.
- **The agent is read-only by construction.** A keyword and single-statement check is the first fence;
  the real protection is a read-only DuckDB connection with external file access disabled, a row
  limit and a timeout.
- **Retrieval keeps a small model focused.** Only the relevant schema chunks and example queries are
  put in the prompt, which matters for a 3B-parameter model.
- **Honest about missing data.** Star-growth columns stay NULL until enough daily history exists, and
  the SQL tool tells the model so, instead of letting it claim that nothing grew.
- **Model backend is isolated** in `agent/llm.py`, so Ollama can be replaced by a hosted API.

## Known limits

- A 3B model sometimes pads answers and is slower than a hosted model (roughly 10 to 70 seconds per
  question on CPU).
- Star-growth questions need about a week of daily Airflow runs before they return numbers.
- The eval set is small and checks values, not wording.

## CI

GitHub Actions runs the unit tests and a full `dbt build` (all models and tests) on a tiny fixture
dataset on every push. The model-dependent evaluation is not run in CI, because CI has no model server.
