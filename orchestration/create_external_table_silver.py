# orchestration/create_external_table_silver.py
from pathlib import Path
from python_terraform import Terraform
from google.cloud import bigquery
from typing import Dict, Any


def get_terraform_outputs(tf_dir: Path) -> Dict[str, Any]:
    """
    This function fetches the outputs from the Terraform state file located in the specified directory.
    """
    print("Fetching infrastructure details from Terraform...")

    tf = Terraform(working_dir=str(tf_dir))
    result = tf.output(json=True)

    outputs = {key: value["value"] for key, value in result.items()}

    required_keys = [
        "project_id",
        "silver_bucket_name",
        "silver_dataset_id",
    ]
    if not all(key in outputs for key in required_keys):
        raise ValueError("Missing required Terraform outputs.")

    print("Successfully fetched Terraform outputs.")
    return outputs


def create_silver_external_table(
    project_id: str,
    dataset_id: str,
    bucket_name: str,
    table_name: str = "stg_hackernews_items",
) -> None:
    bq_client = bigquery.Client(project=project_id)
    table_ref = f"{project_id}.{dataset_id}.{table_name}"

    create_table_sql = f"""
    CREATE OR REPLACE EXTERNAL TABLE `{table_ref}`
    WITH PARTITION COLUMNS (
        ingest_date STRING
    )
    OPTIONS (
        format='PARQUET',
        uris=['gs://{bucket_name}/silver/items/*'],
        hive_partition_uri_prefix='gs://{bucket_name}/silver/items/',
        require_hive_partition_filter=false
    );
    """

    print(f"Creating or replacing external table {table_ref}...")
    query_job = bq_client.query(create_table_sql)
    query_job.result()  # Wait for the job to complete
    print(f"External table {table_ref} created or replaced successfully.")


def run_create_external_table() -> None:
    tf_dir = Path(__file__).parent.parent / "infra" / "terraform"
    outputs = get_terraform_outputs(tf_dir)

    project_id = outputs["project_id"]
    silver_bucket_name = outputs["silver_bucket_name"]
    silver_dataset_id = outputs["silver_dataset_id"]

    print(f"GCP Project ID: {project_id}")
    print(f"Silver Bucket: {silver_bucket_name}")
    print(f"Silver Dataset ID: {silver_dataset_id}")
    print("--------------------------")

    print("Starting to create external table in BigQuery...")

    create_silver_external_table(
        project_id=project_id,
        dataset_id=silver_dataset_id,
        bucket_name=silver_bucket_name,
    )

    print("Finished creating external table.")
    print("--------------------------")


if __name__ == "__main__":
    run_create_external_table()
