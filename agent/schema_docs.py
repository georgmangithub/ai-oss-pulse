"""Hand-written descriptions of the marts, embedded into FAISS for retrieval.

Each chunk is small and self-contained so a retrieved chunk is useful on its own.
The tables below are the only ones the agent may query.
"""

CHUNKS = [
    {
        "id": "mart_framework_momentum",
        "text": (
            "Table mart_framework_momentum: latest snapshot for 10 curated AI frameworks "
            "(e.g. LangChain, AutoGPT, Dify). One row per framework. Columns: framework_name, "
            "category, full_name (owner/repo), snapshot_date, star_count, fork_count, "
            "open_issue_count, stars_gained_1d, stars_gained_7d, stars_gained_30d, last_push_at. "
            "stars_gained_* are NULL until enough daily history has been collected. "
            "Use this for questions about popular or fast-growing frameworks."
        ),
    },
    {
        "id": "dim_repo",
        "text": (
            "Table dim_repo: one row per GitHub repo (about 1000) found under topics llm, "
            "ai-agents, rag, machine-learning. Columns: repo_key (lower-case owner/name, join key), "
            "repo_id, full_name, owner, description, language, license, topics (list of text), "
            "created_at, html_url. Use for questions about languages, licenses, topics or owners."
        ),
    },
    {
        "id": "fct_repo_daily",
        "text": (
            "Table fct_repo_daily: one row per repo per snapshot_date. Columns: repo_key (join to "
            "dim_repo.repo_key), snapshot_date, star_count, fork_count, open_issue_count, pushed_at, "
            "stars_gained_1d, stars_gained_7d, stars_gained_30d (NULL until enough history). "
            "Use for star counts and growth across all repos; filter snapshot_date to the latest "
            "date with (select max(snapshot_date) from fct_repo_daily) for current numbers."
        ),
    },
    {
        "id": "fct_papers",
        "text": (
            "Table fct_papers: one row per recent arXiv paper (about 1900). Columns: arxiv_id, "
            "paper_url, title, abstract, authors (list of text), primary_category (e.g. cs.LG, cs.CL, "
            "cs.AI), categories (list of text), published_at, updated_at. "
            "Use for counting papers by category or date. For topic questions use search_papers."
        ),
    },
    {
        "id": "example_top_frameworks",
        "text": (
            "Example. Question: which frameworks have the most stars? SQL: select framework_name, "
            "star_count from mart_framework_momentum order by star_count desc limit 5"
        ),
    },
    {
        "id": "example_language_counts",
        "text": (
            "Example. Question: which programming languages are most common among repos? SQL: "
            "select language, count(*) as repos from dim_repo where language is not null "
            "group by language order by repos desc limit 10"
        ),
    },
    {
        "id": "example_top_repos",
        "text": (
            "Example. Question: what are the 10 most starred repos? SQL: select r.full_name, "
            "d.star_count from fct_repo_daily d join dim_repo r using (repo_key) "
            "where d.snapshot_date = (select max(snapshot_date) from fct_repo_daily) "
            "order by d.star_count desc limit 10"
        ),
    },
    {
        "id": "example_papers_by_category",
        "text": (
            "Example. Question: how many papers per category? SQL: select primary_category, "
            "count(*) as papers from fct_papers group by primary_category order by papers desc"
        ),
    },
    {
        "id": "example_list_unnest",
        "text": (
            "Example. Question: which GitHub topics are most common? SQL: select topic, count(*) "
            "as repos from (select unnest(topics) as topic from dim_repo) group by topic "
            "order by repos desc limit 10. Note: list columns (topics, authors, categories) "
            "are read with unnest(...)."
        ),
    },
]
