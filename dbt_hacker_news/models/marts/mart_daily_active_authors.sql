-- models/marts/mart_daily_active_authors.sql
WITH fct_stories AS (
    SELECT *
    FROM {{ ref('fct_stories')}}
)

SELECT
    CAST(created_at AS DATE) AS story_date,
    COUNT(DISTINCT user_key) AS active_authors_per_day
FROM fct_stories
GROUP BY story_date
ORDER BY story_date DESC
