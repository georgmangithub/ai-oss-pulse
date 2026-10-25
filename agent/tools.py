import re
import threading
from pathlib import Path

import duckdb

DB_PATH = Path("data/lakehouse/warehouse.duckdb")
MAX_ROWS = 50
TIMEOUT_SECONDS = 10

_FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|create|alter|attach|detach|copy|export|import|install|load|"
    r"pragma|call|set|truncate|replace|read_\w+|glob)\b",
    re.IGNORECASE,
)


class UnsafeSQL(ValueError):
    pass


def check_sql(sql: str) -> str:
    """Return a cleaned single SELECT statement, or raise UnsafeSQL."""
    cleaned = re.sub(r"--[^\n]*|/\*.*?\*/", " ", sql, flags=re.DOTALL).strip().rstrip(";").strip()
    if ";" in cleaned:
        raise UnsafeSQL("Only one statement is allowed.")
    if not re.match(r"(select|with)\b", cleaned, re.IGNORECASE):
        raise UnsafeSQL(
            "Only SELECT queries are allowed. This assistant is read-only: tell the user "
            "you cannot modify data and stop."
        )
    match = _FORBIDDEN.search(cleaned)
    if match:
        raise UnsafeSQL(f"Keyword not allowed: {match.group(0)}")
    return cleaned


def run_sql(sql: str) -> dict:
    """Run a read-only query. Returns {"columns", "rows"} or {"error"} the model can react to."""
    try:
        cleaned = check_sql(sql)
    except UnsafeSQL as exc:
        return {"error": str(exc)}

    # Read-only + no file access are the real protection; check_sql is the first fence.
    conn = duckdb.connect(
        str(DB_PATH), read_only=True, config={"enable_external_access": False}
    )
    timer = threading.Timer(TIMEOUT_SECONDS, conn.interrupt)
    timer.start()
    try:
        cursor = conn.execute(f"select * from ({cleaned}) limit {MAX_ROWS}")
        columns = [d[0] for d in cursor.description]
        rows = [[_plain(v) for v in row] for row in cursor.fetchall()]
        result = {"columns": columns, "rows": rows}
        if "stars_gained" in cleaned.lower() and _growth_all_null(conn):
            result["note"] = (
                "stars_gained_1d/7d/30d are NULL for every repo: only one day of history has "
                "been collected. Tell the user growth cannot be computed yet."
            )
        return result
    except duckdb.Error as exc:
        return {"error": f"SQL error: {exc}"}
    finally:
        timer.cancel()
        conn.close()


def _growth_all_null(conn) -> bool:
    try:
        return conn.execute("select count(stars_gained_7d) from fct_repo_daily").fetchone()[0] == 0
    except duckdb.Error:
        return False


def _plain(value):
    """Make a DuckDB value JSON-friendly."""
    if isinstance(value, (int, float, str, bool, type(None))):
        return value
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    return str(value)
