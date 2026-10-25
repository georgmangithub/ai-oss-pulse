-- One row per repo per snapshot, with star changes versus earlier snapshots.
-- Changes are null until a repo has a snapshot at least N days older.
with daily as (

    select repo_key, snapshot_date, star_count
    from {{ ref('stg_github_repos') }}

),

with_prior as (

    select
        d.repo_key,
        d.snapshot_date,
        d.star_count,
        -- latest snapshot at or before N days ago, via an as-of join
        p1.star_count  as stars_1d_ago,
        p7.star_count  as stars_7d_ago,
        p30.star_count as stars_30d_ago
    from daily d
    asof left join daily p1
        on d.repo_key = p1.repo_key and d.snapshot_date - 1 >= p1.snapshot_date
    asof left join daily p7
        on d.repo_key = p7.repo_key and d.snapshot_date - 7 >= p7.snapshot_date
    asof left join daily p30
        on d.repo_key = p30.repo_key and d.snapshot_date - 30 >= p30.snapshot_date

)

select
    repo_key,
    snapshot_date,
    star_count,
    star_count - stars_1d_ago  as stars_gained_1d,
    star_count - stars_7d_ago  as stars_gained_7d,
    star_count - stars_30d_ago as stars_gained_30d
from with_prior
