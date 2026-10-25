import json
import os
import time
from datetime import date
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://api.github.com/search/repositories"
RAW_DIR = Path("data/raw/github/repos")

def _headers() -> dict:
    headers = {"Accept": "application/vnd.github+json"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers

def _get(params: dict) -> requests.Response:
    """GET with rate-limit awareness."""
    while True:
        resp = requests.get(API_URL, params=params, headers=_headers(), timeout=30)
        remaining = int(resp.headers.get("X-RateLimit-Remaining", 1))
        if resp.status_code in (403, 429) and remaining == 0:
            reset = int(resp.headers["X-RateLimit-Reset"])
            wait = max(reset - time.time(), 0) + 1
            print(f"Rate limited. Sleeping {wait:.0f}s")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp


def fetch_topic(topic: str, max_pages: int = 3) -> list[dict]:
    items = []
    for page in range(1, max_pages + 1):
        params = {
            "q": f"topic:{topic}",
            "sort": "stars",
            "order": "desc",
            "per_page": 100,
            "page": page,
        }
        batch = _get(params).json()["items"]
        items.extend(batch)
        if len(batch) < 100:  # last page
            break
        time.sleep(2)  # be polite; search API is also limited per minute
    return items


def run(topics=("llm", "ai-agents", "rag", "machine-learning")) -> Path:
    today = date.today().isoformat()
    repos = {}
    for topic in topics:
        for repo in fetch_topic(topic):
            repos[repo["full_name"]] = repo  # dedupe repos in several topics

    out_dir = RAW_DIR / f"dt={today}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "repos.json"
    out_file.write_text(json.dumps(list(repos.values())), encoding="utf-8")
    print(f"Wrote {len(repos)} repos to {out_file}")
    return out_file


if __name__ == "__main__":
    run()