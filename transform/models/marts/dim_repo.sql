-- One row per repo: its latest known attributes.
with ranked as (

    select
        *,
        row_number() over (partition by repo_key order by snapshot_date desc) as rn
    from {{ ref('stg_github_repos') }}

)

select
    repo_key,
    repo_id,
    full_name,
    owner,
    description,
    language,
    license,
    topics,
    created_at,
    html_url
from ranked
where rn = 1
