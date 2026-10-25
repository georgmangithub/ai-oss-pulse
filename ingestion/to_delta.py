import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pyarrow as pa
from deltalake import write_deltalake

RAW = Path("data/raw")
BRONZE = Path("data/lakehouse/bronze")
ATOM = "{http://www.w3.org/2005/Atom}"
ARXIV = "{http://arxiv.org/schemas/atom}"

GITHUB_SCHEMA = pa.schema([
    ("repo_id", pa.int64()),
    ("full_name", pa.string()),
    ("owner", pa.string()),
    ("description", pa.string()),
    ("language", pa.string()),
    ("license", pa.string()),
    ("topics", pa.list_(pa.string())),
    ("stars", pa.int64()),
    ("forks", pa.int64()),
    ("open_issues", pa.int64()),
    ("created_at", pa.string()),
    ("pushed_at", pa.string()),
    ("html_url", pa.string()),
    ("dt", pa.string()),
])

ARXIV_SCHEMA = pa.schema([
    ("paper_id", pa.string()),
    ("title", pa.string()),
    ("summary", pa.string()),
    ("authors", pa.list_(pa.string())),
    ("primary_category", pa.string()),
    ("categories", pa.list_(pa.string())),
    ("published", pa.string()),
    ("updated", pa.string()),
    ("dt", pa.string()),
])


def latest_dt(source_dir: Path) -> str:
    return max(p.name.removeprefix("dt=") for p in source_dir.glob("dt=*"))


def github_rows(dt: str) -> list[dict]:
    repos = json.loads(
        (RAW / "github/repos" / f"dt={dt}" / "repos.json").read_text(encoding="utf-8")
    )
    return [
        {
            "repo_id": r["id"],
            "full_name": r["full_name"],
            "owner": r["owner"]["login"],
            "description": r.get("description"),
            "language": r.get("language"),
            "license": (r.get("license") or {}).get("spdx_id"),
            "topics": r.get("topics", []),
            "stars": r["stargazers_count"],
            "forks": r["forks_count"],
            "open_issues": r["open_issues_count"],
            "created_at": r["created_at"],
            "pushed_at": r["pushed_at"],
            "html_url": r["html_url"],
            "dt": dt,
        }
        for r in repos
    ]


def arxiv_rows(dt: str) -> list[dict]:
    papers = {}  # pages overlap when new papers arrive mid-run, so dedupe by id
    for page in sorted((RAW / "arxiv/papers" / f"dt={dt}").glob("page_*.xml")):
        root = ET.parse(page).getroot()
        for e in root.findall(f"{ATOM}entry"):
            paper_id = e.find(f"{ATOM}id").text.strip()
            papers[paper_id] = {
                "paper_id": paper_id,
                "title": e.find(f"{ATOM}title").text.strip(),
                "summary": e.find(f"{ATOM}summary").text.strip(),
                "authors": [a.find(f"{ATOM}name").text for a in e.findall(f"{ATOM}author")],
                "primary_category": e.find(f"{ARXIV}primary_category").get("term"),
                "categories": [c.get("term") for c in e.findall(f"{ATOM}category")],
                "published": e.find(f"{ATOM}published").text,
                "updated": e.find(f"{ATOM}updated").text,
                "dt": dt,
            }
    return list(papers.values())


def write_partition(name: str, rows: list[dict], schema: pa.Schema, dt: str) -> None:
    table = pa.Table.from_pylist(rows, schema=schema)
    write_deltalake(
        str(BRONZE / name),
        table,
        mode="overwrite",
        partition_by=["dt"],
        predicate=f"dt = '{dt}'",  # replace only this day's partition
    )
    print(f"{name}: wrote {table.num_rows} rows for dt={dt}")


def run(dt: str | None = None) -> None:
    gh_dt = dt or latest_dt(RAW / "github/repos")
    write_partition("github_repos", github_rows(gh_dt), GITHUB_SCHEMA, gh_dt)
    ax_dt = dt or latest_dt(RAW / "arxiv/papers")
    write_partition("arxiv_papers", arxiv_rows(ax_dt), ARXIV_SCHEMA, ax_dt)


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else None)
