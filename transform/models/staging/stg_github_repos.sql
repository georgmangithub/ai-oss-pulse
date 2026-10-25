with source as (

    select * from {{ source('bronze', 'github_repos') }}

),

renamed as (

    select
        repo_id,
        full_name,
        lower(full_name)                as repo_key,
        owner,
        description,
        language,
        license,
        topics,
        stars                           as star_count,
        forks                           as fork_count,
        open_issues                     as open_issue_count,
        cast(created_at as timestamptz) as created_at,
        cast(pushed_at as timestamptz)  as pushed_at,
        html_url,
        cast(dt as date)                as snapshot_date
    from source

)

select * from renamed
