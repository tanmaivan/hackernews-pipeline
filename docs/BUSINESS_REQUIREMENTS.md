# Business Requirements for the Hacker News Data Warehouse

Version: 1.0
Date: 2025-10-05
Owner: Tan Mai Van

## 1. Overview

This document outlines the key business requirements, data consumers, and critical metrics that the Hacker News data warehouse is designed to support. The Gold Layer of the warehouse is specifically architected to answer these questions and serve these consumers directly.

## 2. Data Consumers & Their Needs

This data platform serves multiple stakeholders, each with distinct requirements:

| Consumer Group             | Key Needs & Questions                                                                                                                                                                                                                                                                            |
| :------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Product Managers (PMs)** | - **Top-line Metrics:** How many stories are posted per day? How many authors are active? What is the overall engagement (comments, score)? <br> - **Trend Analysis:** How are these metrics changing over time? <br> - **Drill-Downs:** Ability to filter metrics by day, item type, or author. |
| **Data Analysts & BI**     | - **Ad-Hoc Analysis:** Freedom to explore trends, perform cohort analysis, and build funnels. <br> - **Reliable Foundation:** Access to clean, standardized tables with clear primary/foreign keys and a robust time dimension.                                                                  |
| **Data Scientists & ML**   | - **Feature Engineering:** Need data to build a feature store for models (e.g., author reputation, story virality prediction). <br> - **Historical Data:** Access to historical snapshots of item states (how score/comments changed over time).                                                 |
| **Monitoring / SRE**       | - **Operational Health:** Dashboards on data freshness, pipeline failures, ingestion volumes, and data quality anomalies.                                                                                                                                                                        |

## 3. Key Business Metrics & Definitions

The following metrics are prioritized for implementation in the Gold Layer. Each metric should be clearly defined, owned, and have a freshness Service Level Agreement (SLA).

### Tier A (High Priority - Core Health Metrics)

| Metric ID | Metric Name                | Definition (Conceptual)                                                                    | SQL Logic (in dbt)                                                  |
| :-------- | :------------------------- | :----------------------------------------------------------------------------------------- | :------------------------------------------------------------------ |
| M01       | **Stories per Day**        | The total count of new items of type 'story' created on a given day.                       | `COUNT(item_key) FROM fct_stories GROUP BY created_date`            |
| M02       | **Active Authors per Day** | The unique count of authors who posted at least one item on a given day.                   | `COUNT(DISTINCT user_key) FROM fct_stories GROUP BY created_date`   |
| M03       | **Median Score per Story** | The median score of all stories created on a given day, reflecting typical engagement.     | `APPROX_QUANTILES(score, 100)[OFFSET(50)]`                          |
| M04       | **Avg Comments per Story** | The average number of comments (descendants) for stories created on a given day.           | `AVG(comment_count)`                                                |
| M05       | **Top Authors by Score**   | A ranked list of authors based on the sum of scores from their stories over a time period. | `SUM(score) OVER (PARTITION BY user_key)`                           |
| M06       | **Time to First Comment**  | The average time (in minutes) between a story's creation and its first comment.            | `AVG(timestamp_diff(first_comment_ts, story_created_ts, 'MINUTE'))` |

### Tier B (Deeper Analytics)

| Metric ID | Metric Name                 | Definition (Conceptual)                                                                 |
| :-------- | :-------------------------- | :-------------------------------------------------------------------------------------- |
| M07       | **7-Day Story Engagement**  | The percentage of stories that receive at least one comment within 7 days of creation.  |
| M08       | **Comment Rate**            | The ratio of comments to stories over a given period.                                   |
| M09       | **Author Lifetime Metrics** | The duration between an author's first and last known post, and their total post count. |

### Data Quality & Observability Metrics

| Metric ID | Metric Name             | Definition (Conceptual)                                                                            |
| :-------- | :---------------------- | :------------------------------------------------------------------------------------------------- |
| DQ01      | **Ingestion Latency**   | The time difference between the pipeline processing time (`ingest_ts`) and the current time.       |
| DQ02      | **Missing Fields Rate** | The percentage of raw records missing critical fields like `item_id`, `created_at`, or `author`.   |
| DQ03      | **Partition Coverage**  | A daily check to ensure that data for the previous day has been successfully loaded and processed. |
