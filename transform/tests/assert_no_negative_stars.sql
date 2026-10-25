-- Singular test: any returned row is a failure.
select * from {{ ref('fct_repo_daily') }}
where star_count < 0 or fork_count < 0
