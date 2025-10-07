-- models/marts/mart_daily_story_metrics.sql
WITH fct_stories AS (
    SELECT *
    FROM {{ ref('fct_stories')}}
)

SELECT
    CAST(created_at AS DATE) AS story_date,
    COUNT(item_key) AS stories_per_day,
    AVG(total_comments) AS avg_comments_per_story,
    APPROX_QUANTILES(score, 10)[OFFSET(5)] AS median_story_score,
FROM fct_stories
GROUP BY story_date
ORDER BY story_date DESC
