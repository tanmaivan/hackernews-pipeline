-- models/marts/dimensions/dim_users.sql
WITH
    stg_items AS (
        SELECT *
        FROM {{ ref('stg_hn_items')}}
    ),
    user_metrics AS (
        SELECT
            author,
            MIN(created_at) AS first_post_at_ts,
            MAX(created_at) AS last_post_at_ts,
            COUNT(*) AS total_posts_count
        FROM stg_items
        WHERE author IS NOT NULL
        GROUP BY author
    )

SELECT
    {{ dbt_utils.generate_surrogate_key(['author']) }} AS user_key,
    author AS user_name,
    first_post_at_ts, last_post_at_ts,
    total_posts_count,
    TIMESTAMP_DIFF(last_post_at_ts, first_post_at_ts, DAY) AS author_lifetime_days
FROM user_metrics

UNION ALL

SELECT
    'unknown_user_key' AS user_key,
    'unknown_user_name' AS user_name,
    NULL AS first_post_at_ts,
    NULL AS last_post_at_ts,
    0 AS total_posts_count,
    NULL AS author_lifetime_days
