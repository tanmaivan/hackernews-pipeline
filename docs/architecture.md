# Project Architecture

This document provides a detailed breakdown of the system architecture and data flow.

## 1. Architectural Pattern

The platform is built on a modern **ELT (Extract - Load - Transform)** architecture, combined with the **Medallion (Bronze, Silver, Gold)** framework for structuring data layers.

- **Extract & Load:** Data is extracted from the source and loaded into our data platform with minimal transformation.
- **Transform:** All complex transformations, modeling, and business logic are executed directly within the data warehouse (BigQuery), orchestrated by dbt.

## 2. System Diagram

![Architecture Diagram](./images/architecture.png)

## 3. Data Flow Explained

1.  **Foundation (Terraform):** `Terraform` provisions all necessary GCP resources (GCS, BigQuery, IAM) from code.
2.  **Orchestration (Prefect):** `Prefect` acts as the central orchestrator, scheduling and triggering all pipeline tasks.
3.  **Bronze Layer (Ingestion):** A Prefect flow runs a Python script to extract raw JSON data from the Hacker News API and loads it into a **GCS Bronze Bucket**.
4.  **Silver Layer (Optimization):** Another Prefect flow triggers a BigQuery job that reads the raw JSON, cleans it, and transforms it into partitioned **Parquet** files in a **GCS Silver Bucket**.
5.  **Gold Layer (Modeling):** Prefect triggers `dbt` jobs. dbt reads data from the Silver layer (via an External Table) and executes a series of SQL models to build a Star Schema (Dimensions, Facts) and aggregated Data Marts inside the **BigQuery Gold Dataset**.
6.  **Governance (Data Catalog):** A final automated step syncs all metadata (descriptions, lineage) from the dbt project into **Google Data Catalog**.
7.  **Presentation (Looker Studio):** `Looker Studio` connects directly to the Gold Layer tables in BigQuery to serve the final dashboard to end-users.
