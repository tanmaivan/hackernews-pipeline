### Architectural Decisions (ADRs)

This section documents the rationale behind key technology choices for this project.

#### 1. Why a Serverless ELT Architecture?

- **Decision:** I chose an ELT (Extract-Load-Transform) architecture over a traditional ETL one.
- **Rationale:** Modern cloud data warehouses like BigQuery are extremely powerful. By loading raw data first and using BigQuery's engine for transformations (orchestrated by dbt), we leverage its scalability and performance. This avoids the need to manage and scale a separate transformation server (like a Spark cluster), reducing operational overhead and cost.

#### 2. Why Google Cloud Platform (GCP)?

- **Decision:** The entire platform is built on GCP.
- **Rationale:** GCP offers a suite of tightly integrated, serverless data services. The combination of **GCS** for affordable storage, **BigQuery** for its powerful and cost-effective analytics engine, and **Looker Studio** for free, native BI integration provides a complete and cohesive ecosystem for this project.

#### 3. Why Prefect Cloud for Orchestration?

- **Decision:** Prefect Cloud was chosen as the orchestration platform over alternatives like Apache Airflow.
- **Rationale:** Prefect offers a modern, Python-native workflow paradigm that accelerates development. Key advantages include:
  - **Dynamic Workflows:** Its flexible, code-as-workflows approach is more intuitive than traditional static DAGs.
  - **Managed Observability:** Prefect Cloud provides a rich, out-of-the-box UI for monitoring, logging, and scheduling, eliminating the need to host and manage our own orchestration backend.
  - **Hybrid Execution Model:** The architecture ensures our code and data remain secure within our GCP environment, while Prefect Cloud manages only the orchestration metadata.

#### 4. Why dbt for Transformation?

- **Decision:** All Gold layer transformations are managed by dbt.
- **Rationale:** dbt is the industry standard for analytics engineering. It allows us to treat our transformation logic as code, enabling version control, automated testing, and documentation. This dramatically improves the reliability, maintainability, and trustworthiness of our data models.

#### 5. Why Looker Studio for BI?

- **Decision:** Looker Studio was chosen as the visualization tool.
- **Rationale:** As a free tool with a native, high-performance connector to BigQuery, Looker Studio provides the fastest path from data to insight. Its intuitive interface allows for rapid dashboard development, making it ideal for demonstrating the value of the underlying data platform.
