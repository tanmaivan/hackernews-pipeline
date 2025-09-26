# 0001 - Record architecture decisions

Date: 2025-09-26

## Context

Project will ingest Hacker News -> GCS -> BigQuery -> dbt -> Looker Studio.

## Decision

Adopt Medallion architecture: bronze/silver/gold.

## Consequences

- Need extra pipelines to convert raw -> parquet -> staging -> curated.
- More storage & operational cost but better governance.
