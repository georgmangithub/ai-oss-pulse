import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT = os.environ.get("PROJECT_DIR", "/opt/project")
PY = "/home/airflow/venv/bin/python"
DBT = "/home/airflow/venv/bin/dbt"

default_args = {
    "owner": "george",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="ai_oss_pulse_daily",
    description="Ingest GitHub + arXiv, load bronze Delta tables, build dbt models",
    start_date=datetime(2026, 10, 25),
    schedule="@daily",
    catchup=False,  # ingestion is "as of today"; backfilling would just re-pull today
    default_args=default_args,
    max_active_runs=1,  # DuckDB file allows a single writer
) as dag:
    # The ingestion scripts use paths relative to the repo root, so run from there.
    github = BashOperator(
        task_id="ingest_github",
        bash_command=f"cd {PROJECT} && {PY} -m ingestion.github",
    )
    arxiv = BashOperator(
        task_id="ingest_arxiv",
        bash_command=f"cd {PROJECT} && {PY} -m ingestion.arxiv",
    )
    bronze = BashOperator(
        task_id="raw_to_delta",
        bash_command=f"cd {PROJECT} && {PY} -m ingestion.to_delta",
    )
    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=f"cd {PROJECT}/transform && {DBT} --no-partial-parse build --profiles-dir .",
    )

    [github, arxiv] >> bronze >> dbt_build
