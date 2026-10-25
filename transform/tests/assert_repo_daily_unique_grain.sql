-- Singular test: returns rows that violate the grain (repo_key, snapshot_date) of fct_repo_daily.
select repo_key, snapshot_date, count(*) as n
from {{ ref('fct_repo_daily') }}
group by 1, 2
having count(*) > 1
