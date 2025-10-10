# Hacker News Analytics Platform

A comprehensive, end-to-end data platform that extracts, models, and visualizes trends from Hacker News. This project demonstrates a modern data stack on Google Cloud, implementing an ELT architecture with automated orchestration and robust data governance.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Problem Statement](#2-problem-statement)
3. [Architecture](#3-architecture)
4. [Tech Stack](#4-tech-stack)
5. [Key Features](#5-key-features)
6. [Live Dashboard](#6-live-dashboard)
7. [Project Structure](#7-project-structure)
8. [Getting Started](#8-getting-started)
9. [Architectural Decisions (ADRs)](#9-architectural-decisions-adrs)
10. [Contributing](#10-contributing)
11. [License](#11-license)

---

### 1. Overview

This project provides a scalable and automated solution for analyzing Hacker News data. It ingests raw data from the official API, processes it through a multi-layered data platform (Bronze, Silver, Gold), and presents key business metrics on an interactive BI dashboard. The entire infrastructure is managed as code, and the pipeline is orchestrated for daily refreshes.

### 2. Problem Statement

Individual users and organizations often struggle to analyze trends on Hacker News due to the platform's high-volume, unstructured, and transient data. This project solves three core problems:

- **Data Fragmentation:** Automates the collection and structuring of disparate items (stories, comments) from the API.
- **Lack of Historical Storage:** Implements a data warehousing strategy to store data long-term, enabling trend and historical analysis.
- **No Analytical Tooling:** Provides a ready-to-use, curated Gold layer and a BI dashboard to answer key business questions.

### 3. Architecture

The platform is built on a modern, serverless ELT architecture using a Medallion (Bronze, Silver, Gold) framework. All infrastructure is provisioned via Terraform, and pipelines are orchestrated by Prefect.

_For a detailed breakdown of the architecture, components, and data flow, please see the **[Architecture Documentation](./docs/architecture.md)**._

![Architecture Diagram](./docs/images/architecture.png)

### 4. Tech Stack

| Category                   | Technology                  | Purpose                                                     |
| :------------------------- | :-------------------------- | :---------------------------------------------------------- |
| **Cloud Provider**         | Google Cloud Platform (GCP) | Core infrastructure services.                               |
| **Infrastructure as Code** | Terraform                   | Provisioning GCS, BigQuery, IAM.                            |
| **Orchestration**          | Prefect                     | Scheduling and monitoring all data pipelines.               |
| **Data Lake / Staging**    | GCS (Bronze & Silver)       | Storage for raw JSON and optimized Parquet files.           |
| **Data Warehouse**         | BigQuery (Gold)             | Storage for curated, business-ready data models.            |
| **Transformation**         | dbt                         | Data modeling, testing, and documentation (Silver -> Gold). |
| **Data Governance**        | Google Data Catalog         | Centralized metadata discovery and management.              |
| **Business Intelligence**  | Looker Studio               | Interactive dashboarding and visualization.                 |
| **Core Language**          | Python                      | Extraction scripts and orchestration logic.                 |

### 5. Key Features

- **Automated ELT Pipeline:** End-to-end orchestration from data ingestion to BI.
- **Dimensional Modeling:** Gold layer is modeled as a Star Schema for optimized analytics.
- **Data Governance:** Automated metadata synchronization between dbt and Google Data Catalog.
- **Infrastructure as Code:** Fully reproducible environment managed by Terraform.

### 6. Live Dashboard

The final output of this project is an interactive Looker Studio dashboard that visualizes key trends and metrics.

_See the **[Dashboard Documentation](./docs/dashboard.md)** for a guide on how to interpret the charts._

**[View Live Dashboard →](https://lookerstudio.google.com/s/i3d2np2Q1SU)**

[![Dashboard Screenshot](./docs/images/dashboard_overview.png)](https://lookerstudio.google.com/s/i3d2np2Q1SU)

_Please be aware that historical data collection for this project started on August 23, 2025. As a result, lifetime metrics such as "Author Lifetime Days" are calculated based on activity observed since this date and may not represent the full history of an author on Hacker News._

### 7. Project Structure

The repository is organized into distinct directories, each with a specific responsibility.

_For a detailed explanation of each directory, please see the **[Repository Structure Guide](./docs/repository_structure.md)**._

### 8. Getting Started

To set up and run this project locally, please follow the detailed instructions in the **[Project Setup Guide](./docs/setup.md)**. The guide covers prerequisites, environment configuration, and step-by-step commands to provision the infrastructure and run the pipelines.

### 9. Architectural Decisions (ADRs)

Key architectural decisions are documented to provide context and rationale for the chosen technical approaches.

_See the **[Architectural Decision Records](./adr/)** for more details._
