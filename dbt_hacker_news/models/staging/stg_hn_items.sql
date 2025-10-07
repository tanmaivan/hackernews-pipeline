--- dbt_hackernews/models/staging/stg_hn_items.sql

WITH source AS (
    SELECT *
    FROM {{ source('hackernews_silver_external', 'stg_hackernews_items') }}
)

SELECT
    item_id, parent_id,
    created_at, ingest_date_str,
    author,
    item_type, title, text_content, url,
    score, descendants,
    source_file,
    ingest_date
FROM source
