import duckdb
import pytest

from agent import tools


@pytest.mark.parametrize(
    "sql",
    [
        "drop table dim_repo",
        "select 1; select 2",
        "delete from dim_repo",
        "select * from read_csv('x.csv')",
        "copy dim_repo to 'x.csv'",
        "attach 'other.db'",
        "-- sneaky\ndrop table dim_repo",
        "insert into dim_repo values (1)",
    ],
)
def test_unsafe_sql_rejected(sql):
    assert "error" in tools.run_sql(sql)


def test_check_sql_strips_comments_and_semicolon():
    assert tools.check_sql("/* hi */ select 1 as x; ") == "select 1 as x"


def test_with_query_allowed():
    assert tools.check_sql("with a as (select 1 as x) select * from a")


def test_run_sql_limits_rows_and_reports_errors(tmp_path, monkeypatch):
    db = tmp_path / "t.duckdb"
    conn = duckdb.connect(str(db))
    conn.execute("create table dim_repo as select range as n from range(200)")
    conn.close()
    monkeypatch.setattr(tools, "DB_PATH", db)

    result = tools.run_sql("select n from dim_repo")
    assert len(result["rows"]) == tools.MAX_ROWS

    assert "error" in tools.run_sql("select nope from dim_repo")
