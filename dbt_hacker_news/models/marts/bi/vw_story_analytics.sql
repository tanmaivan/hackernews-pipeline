{{
    config(
        materialized='view'
    )
}}

WITH
    fct_stories AS (
        SELECT *
        FROM {{ ref('fct_stories')}}
    ),
    dim_items AS (
        SELECT *
        FROM {{ ref('dim_items')}}
    ),
    dim_users AS (
        SELECT *
        FROM {{ ref('dim_users')}}
    )

SELECT
    -- Story details
    fs.item_key, di.item_id, di.title, di.url, di.domain AS story_domain,
    -- Author details
    fs.user_key, du.user_name, du.author_lifetime_days, du.total_posts_count,
    -- Time details
    fs.created_at, CAST(fs.created_at AS DATE) AS created_at_date,
    -- Story metrics
    fs.score, fs.total_comments, fs.time_to_first_comment_seconds
FROM fct_stories fs
LEFT JOIN dim_items di ON fs.item_key = di.item_key
LEFT JOIN dim_users du ON fs.user_key = du.user_key
