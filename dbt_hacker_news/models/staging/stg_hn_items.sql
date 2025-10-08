--- dbt_hackernews/models/staging/stg_hn_items.sql

WITH
    source AS (
        SELECT *
        FROM {{ source('hackernews_silver_external', 'stg_hackernews_items') }}
    ),
    deduped AS (
        SELECT
            *,
            ROW_NUMBER() OVER (PARTITION BY item_id ORDER BY ingest_date DESC) AS row_num
        FROM source
    )

SELECT
    item_id, parent_id,
    created_at, ingest_date_str,
    author,
    item_type, title, text_content, url,
    score, descendants,
    source_file,
    ingest_date
FROM deduped
WHERE row_num = 1
