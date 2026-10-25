with source as (

    select * from {{ source('bronze', 'arxiv_papers') }}

),

cleaned as (

    select
        paper_id                                                  as paper_url,
        regexp_extract(paper_id, 'abs/(.+?)(v[0-9]+)?$', 1)       as arxiv_id,
        regexp_replace(title, '\s+', ' ', 'g')                    as title,
        regexp_replace(summary, '\s+', ' ', 'g')                  as abstract,
        authors,
        primary_category,
        categories,
        cast(published as timestamptz)                            as published_at,
        cast(updated as timestamptz)                              as updated_at,
        cast(dt as date)                                          as snapshot_date
    from source

)

select * from cleaned
