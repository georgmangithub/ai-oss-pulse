import time
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests

API_URL = "http://export.arxiv.org/api/query"
RAW_DIR = Path("data/raw/arxiv/papers")
ATOM = {"a": "http://www.w3.org/2005/Atom"}
PAGE_SIZE = 100


def _fetch_page(start: int) -> str:
    params = {
        "search_query": "cat:cs.AI OR cat:cs.CL OR cat:cs.LG",
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "start": start,
        "max_results": PAGE_SIZE,
    }
    resp = requests.get(API_URL, params=params, timeout=60)
    resp.raise_for_status()
    return resp.text


def _published_dates(xml_text: str) -> list[datetime]:
    root = ET.fromstring(xml_text)
    return [
        datetime.fromisoformat(e.find("a:published", ATOM).text.replace("Z", "+00:00"))
        for e in root.findall("a:entry", ATOM)
    ]


def run(days_back: int = 7, max_pages: int = 30) -> Path:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
    out_dir = RAW_DIR / f"dt={date.today().isoformat()}"
    out_dir.mkdir(parents=True, exist_ok=True)

    total = 0
    for page in range(max_pages):
        xml_text = _fetch_page(start=page * PAGE_SIZE)
        dates = _published_dates(xml_text)
        if not dates:  # no more results
            break

        (out_dir / f"page_{page:03d}.xml").write_text(xml_text, encoding="utf-8")
        total += len(dates)

        if min(dates) < cutoff:  # we've reached papers older than the window
            break
        time.sleep(3)  # arXiv asks for 1 request / 3 seconds

    print(f"Wrote {total} papers to {out_dir}")
    return out_dir


if __name__ == "__main__":
    run()
