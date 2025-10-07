-- models/marts/dimensions/dim_user.sql
with stg_items AS (
    SELECT *
    FROM {{ ref('stg_hn_items')}}
)

SELECT
    {{ dbt_utils.generate_surrogate_key(['item_id'])}} AS item_key,
    item_id,
    item_type,
    title,
    text_content,
    url,
    {{ dbt_utils.get_url_host('url')}} as domain,
    (url IS NOT NULL) AS has_url,
    length(text_content) AS text_length
FROM stg_items
