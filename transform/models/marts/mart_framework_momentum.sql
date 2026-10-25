-- Latest snapshot for each curated framework: the table the agent queries most.
with latest as (

    select max(snapshot_date) as snapshot_date from {{ ref('fct_repo_daily') }}

)

select
    f.framework_name,
    f.category,
    r.full_name,
    d.snapshot_date,
    d.star_count,
    d.fork_count,
    d.open_issue_count,
    d.stars_gained_1d,
    d.stars_gained_7d,
    d.stars_gained_30d,
    d.pushed_at as last_push_at
from {{ ref('tracked_frameworks') }} f
join {{ ref('dim_repo') }} r
    on lower(f.full_name) = r.repo_key
join {{ ref('fct_repo_daily') }} d
    on r.repo_key = d.repo_key
join latest l
    on d.snapshot_date = l.snapshot_date
