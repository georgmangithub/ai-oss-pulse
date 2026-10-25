-- Grain: one row per paper (latest snapshot wins when a paper was seen on several days).
with ranked as (

    select
        *,
        row_number() over (partition by arxiv_id order by snapshot_date desc) as rn
    from {{ ref('stg_arxiv_papers') }}

)

select
    arxiv_id,
    paper_url,
    title,
    abstract,
    authors,
    primary_category,
    categories,
    published_at,
    updated_at
from ranked
where rn = 1
