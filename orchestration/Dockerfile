FROM apache/airflow:2.10.5-python3.12

# Pipeline dependencies live in their own venv so they can't clash with
# Airflow's pinned packages. DAG tasks call /home/airflow/venv/bin/python directly.
COPY requirements.txt /tmp/requirements.txt
RUN python -m venv /home/airflow/venv && /home/airflow/venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt
