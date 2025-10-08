-- models/marts/facts/fct_stories.sql
WITH
    stg_items AS (
        SELECT *
        FROM {{ ref('stg_hn_items') }}
        WHERE item_type = 'story'
    ),
    dim_items AS (
        SELECT *
        FROM {{ ref('dim_items') }}
    ),
    dim_users AS (
        SELECT *
        FROM {{ ref('dim_users') }}
    ),
    first_comment_time AS (
        SELECT
            parent_id AS story_id,
            MIN(created_at) AS first_comment_at
        FROM {{ ref('stg_hn_items') }}
        WHERE
            item_type = 'comment'
            AND parent_id IN (
                SELECT item_id
                FROM {{ ref('stg_hn_items') }}
                WHERE item_type = 'story'
            )
            GROUP BY parent_id
    ),
    comments_per_story AS (
        SELECT
            parent_id AS story_id,
            COUNT(*) AS total_comments
        FROM {{ ref('stg_hn_items') }}
        WHERE
            item_type = 'comment'
            AND parent_id IN (
                SELECT item_id
                FROM {{ ref('stg_hn_items') }}
                WHERE item_type = 'story'
            )
            GROUP BY parent_id
    )

SELECT
    di.item_key,
    du.user_key,
    CAST(FORMAT_TIMESTAMP('%Y%m%d', si.created_at) AS INT64) AS created_date_key,
    si.created_at,
    si.score,
    cps.total_comments,
    TIMESTAMP_DIFF(fct.first_comment_at, si.created_at, MINUTE) AS time_to_first_comment_minutes
FROM stg_items si
LEFT JOIN dim_items di ON si.item_id = di.item_id
LEFT JOIN dim_users du ON COALESCE(si.author, 'unknown_user_name') = du.user_name
LEFT JOIN first_comment_time fct ON si.item_id = fct.story_id
LEFT JOIN comments_per_story cps ON si.item_id = cps.story_id
