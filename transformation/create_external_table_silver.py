# transformation/create_external_table_silver.py
from pathlib import Path
from python_terraform import Terraform
from typing import Dict, Any
from extractor.src.gcs_utils import get_bq_client
from prefect_gcp import GcpCredentials

gcp_credentials_block = GcpCredentials.load("gcp-creds")

# If you want to use without Prefect, uncomment the line below and comment the line above. But you have to set the environment variable GOOGLE_APPLICATION_CREDENTIALS to point to your service account key file or use other authentication methods provided by google-cloud library
# gcp_credentials_block = GcpCredentials()


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
    table_name: str,
    gcp_credentials_block,
) -> None:
    bq_client = get_bq_client(gcp_credentials_block)
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


def run_create_external_table(
    GCP_PROJECT_ID: str,
    SILVER_DATASET_ID: str,
    SILVER_BUCKET: str,
    gcp_credentials_block,
) -> None:
    """
    This function orchestrates the creation of an external table in BigQuery.
    """

    print(f"GCP Project ID: {GCP_PROJECT_ID}")
    print(f"Silver Bucket: {SILVER_BUCKET}")
    print(f"Silver Dataset ID: {SILVER_DATASET_ID}")
    print("--------------------------")

    print("Starting to create external table in BigQuery...")

    create_silver_external_table(
        project_id=GCP_PROJECT_ID,
        dataset_id=SILVER_DATASET_ID,
        bucket_name=SILVER_BUCKET,
        table_name="stg_hackernews_items",
        gcp_credentials_block=gcp_credentials_block,
    )

    print("Finished creating external table.")
    print("--------------------------")


if __name__ == "__main__":
    tf_dir = Path(__file__).parent.parent / "terraform"
    outputs = get_terraform_outputs(tf_dir)

    GCP_PROJECT_ID = outputs["project_id"]
    SILVER_BUCKET = outputs["silver_bucket_name"]
    SILVER_DATASET_ID = outputs["silver_dataset_id"]

    run_create_external_table(
        GCP_PROJECT_ID=GCP_PROJECT_ID,
        SILVER_DATASET_ID=SILVER_DATASET_ID,
        SILVER_BUCKET=SILVER_BUCKET,
        gcp_credentials_block=gcp_credentials_block,
    )
