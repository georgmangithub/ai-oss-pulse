-- Grain: one row per repo per snapshot date.
select
    s.repo_key,
    s.snapshot_date,
    s.star_count,
    s.fork_count,
    s.open_issue_count,
    s.pushed_at,
    c.stars_gained_1d,
    c.stars_gained_7d,
    c.stars_gained_30d
from {{ ref('stg_github_repos') }} s
join {{ ref('int_repo_star_changes') }} c
    on s.repo_key = c.repo_key and s.snapshot_date = c.snapshot_date
