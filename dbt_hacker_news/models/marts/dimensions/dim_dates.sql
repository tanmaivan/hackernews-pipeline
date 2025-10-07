-- models/marts/dimensions/dim_dates.sql
WITH date_spine AS (
    {{ dbt_utils.date_spine(
        datepart='day',
        start_date="CAST('2006-01-01' AS DATE)",
        end_date="CAST('2026-12-31' AS DATE)"
    )}}
)
SELECT *
FROM date_spine
