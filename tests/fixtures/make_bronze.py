"""Write a tiny bronze Delta dataset so CI can run `dbt build` without real data.

Usage (from the repo root): python tests/fixtures/make_bronze.py
Writes under data/lakehouse/bronze, so do not run it over a real lakehouse.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ingestion.to_delta import ARXIV_SCHEMA, GITHUB_SCHEMA, write_partition  # noqa: E402

# (full_name, stars yesterday, stars today); names match the tracked_frameworks seed
REPOS = [
    ("langchain-ai/langchain", 148000, 148400),
    ("langchain-ai/langgraph", 20000, 20100),
    ("crewAIInc/crewAI", 60000, 60080),
]


def github_rows() -> list[dict]:
    rows = []
    for dt, idx in (("2026-10-24", 1), ("2026-10-25", 2)):
        for i, repo in enumerate(REPOS):
            full_name = repo[0]
            rows.append(
                {
                    "repo_id": 1000 + i,
                    "full_name": full_name,
                    "owner": full_name.split("/")[0],
                    "description": f"Fixture repo {full_name}",
                    "language": "Python",
                    "license": "MIT",
                    "topics": ["llm", "ai-agents"],
                    "stars": repo[idx],
                    "forks": 100 + i,
                    "open_issues": 10 + i,
                    "created_at": "2023-01-01T00:00:00Z",
                    "pushed_at": f"{dt}T08:00:00Z",
                    "html_url": f"https://github.com/{full_name}",
                    "dt": dt,
                }
            )
    return rows


def arxiv_rows(dt: str) -> list[dict]:
    return [
        {
            "paper_id": f"http://arxiv.org/abs/2610.0000{i}v1",
            "title": f"Fixture  paper {i}",
            "summary": "A short\n abstract about agents.",
            "authors": ["A. Author", "B. Author"],
            "primary_category": category,
            "categories": [category],
            "published": "2026-10-24T09:00:00Z",
            "updated": "2026-10-24T09:00:00Z",
            "dt": dt,
        }
        for i, category in enumerate(["cs.LG", "cs.CL", "cs.AI"], start=1)
    ]


if __name__ == "__main__":
    rows = github_rows()
    for dt in ("2026-10-24", "2026-10-25"):
        write_partition("github_repos", [r for r in rows if r["dt"] == dt], GITHUB_SCHEMA, dt)
        write_partition("arxiv_papers", arxiv_rows(dt), ARXIV_SCHEMA, dt)
