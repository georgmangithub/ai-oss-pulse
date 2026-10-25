"""Run the eval set: python -m agent.eval   (needs Ollama running)"""
from pathlib import Path

import mlflow
import yaml

from agent import tracking
from agent.ask import load_indexes
from agent.eval.scoring import score
from agent.tools import run_sql

QUESTIONS = Path(__file__).with_name("questions.yml")


def main() -> None:
    specs = yaml.safe_load(QUESTIONS.read_text(encoding="utf-8"))
    schema_index, paper_index = load_indexes(False)

    tracking.setup()
    rows_out = []
    with mlflow.start_run(run_name="eval"):
        mlflow.log_params(tracking.config_params())
        for spec in specs:
            reference = None
            if spec["kind"] == "sql":
                reference = run_sql(spec["reference_sql"])["rows"]
            result = tracking.run_question(spec["question"], schema_index, paper_index)
            passed, reason = score(spec, result["answer"], result["trace"], reference)
            rows_out.append({**result, "passed": passed, "reason": reason, "kind": spec["kind"]})
            print(f"{'PASS' if passed else 'FAIL'}  {result['latency_s']:>5}s  {spec['question']}")
            if not passed:
                print(f"      {reason}\n      answer: {result['answer'][:200]!r}", flush=True)

        n_pass = sum(r["passed"] for r in rows_out)
        accuracy = n_pass / len(rows_out)
        mlflow.log_metrics(
            {
                "accuracy": accuracy,
                "avg_latency_s": sum(r["latency_s"] for r in rows_out) / len(rows_out),
                "sql_error_rate": sum(r["sql_errors"] for r in rows_out)
                / max(1, sum(r["sql_calls"] for r in rows_out)),
            }
        )
        mlflow.log_dict({"results": rows_out}, "eval_results.json")
    print(f"\nAccuracy: {n_pass}/{len(rows_out)} = {accuracy:.0%}")


if __name__ == "__main__":
    main()
