import json
import re
import tempfile
from pathlib import Path
from typing import Dict, List, Any
from google.cloud import bigquery, storage
from python_terraform import Terraform


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
        "bronze_bucket_name",
        "silver_bucket_name",
        "bronze_dataset_id",
    ]
    if not all(key in outputs for key in required_keys):
        raise ValueError("Missing required Terraform outputs.")

    print("Successfully fetched Terraform outputs.")
    return outputs


def load_checkpoint(bucket_name: str, checkpoint_file: str):
    """
    This function loads the checkpoint file from GCS. If it doesn't exist, it initializes an empty checkpoint.
    """
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(checkpoint_file)

    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    tmp_file_path = tmp_file.name

    if blob.exists():
        blob.download_to_filename(tmp_file_path)
    else:
        with open(tmp_file_path, "w") as f:
            json.dump({}, f)

    with open(tmp_file_path) as f:
        checkpoint_data = json.load(f)

    return checkpoint_data, tmp_file_path, blob


def list_bronze_dates(bucket_name: str) -> List[str]:
    from google.cloud import storage

    client = storage.Client()

    blobs = client.list_blobs(bucket_name, prefix="bronze/")
    dates = set()
    for blob in blobs:
        m = re.match(r"bronze/(\d{4})/(\d{2})/(\d{2})/", blob.name)
        if m:
            dates.add(f"{m[1]}-{m[2]}-{m[3]}")
    return sorted(dates)


def get_dates_to_process(
    bronze_bucket: str, checkpoint_data: Dict[str, Any]
) -> List[str]:
    """
    This function determines which ingestion dates need to be processed based on the checkpoint data.
    """
    client = storage.Client()
    dates_to_process = []
    for ingest_date in list_bronze_dates(bronze_bucket):
        ingest_path = f"bronze/{ingest_date.replace('-', '/')}/"
        blobs = list(client.list_blobs(bronze_bucket, prefix=ingest_path))
        file_count = len(blobs)
        total_bytes = sum(blob.size for blob in blobs)

        old_count = checkpoint_data.get(ingest_date, {}).get("file_count")
        old_bytes = checkpoint_data.get(ingest_date, {}).get("total_bytes")

        if old_count != file_count or old_bytes != total_bytes:
            dates_to_process.append(ingest_date)
    return dates_to_process


def process_dates_in_bq(
    dates_to_process: List[str],
    gcp_project: str,
    bronze_dataset: str,
    bronze_bucket: str,
    silver_bucket: str,
    checkpoint_data: Dict[str, Any],
) -> None:
    """
    This function processes the specified ingestion dates in BigQuery.
    """
    bq_client = bigquery.Client(project=gcp_project)
    storage_client = storage.Client()

    for ingest_date in dates_to_process:
        ingest_date_path = ingest_date.replace("-", "/")
        temp_table_name = f"temp_hn_raw_{ingest_date.replace('-', '')}"
        silver_output_path = (
            f"gs://{silver_bucket}/silver/items/ingest_date={ingest_date}/"
        )

        bq_script = f"""
        CREATE OR REPLACE EXTERNAL TABLE `{gcp_project}.{bronze_dataset}.{temp_table_name}`
        (raw_line STRING)
        OPTIONS(
            format='CSV',
            field_delimiter='§',
            skip_leading_rows=0,
            uris=['gs://{bronze_bucket}/bronze/{ingest_date_path}/*.jsonl.gz']
        );

        EXPORT DATA OPTIONS(
            uri='{silver_output_path}data_*.parquet',
            format='PARQUET',
            overwrite=true,
            compression='SNAPPY'
        ) AS
        WITH parsed_json AS (
            SELECT SAFE.PARSE_JSON(t.raw_line) AS json_obj, _FILE_NAME
            FROM `{gcp_project}.{bronze_dataset}.{temp_table_name}` AS t
        )
        SELECT
            SAFE_CAST(JSON_EXTRACT_SCALAR(json_obj, '$.id') AS INT64) AS item_id,
            JSON_EXTRACT_SCALAR(json_obj, '$.type') AS item_type,
            JSON_EXTRACT_SCALAR(json_obj, '$.by') AS author,
            TIMESTAMP_SECONDS(SAFE_CAST(JSON_EXTRACT_SCALAR(json_obj, '$.time') AS INT64)) as created_at,
            JSON_EXTRACT_SCALAR(json_obj, '$.title') AS title,
            JSON_EXTRACT_SCALAR(json_obj, '$.text') AS text_content,
            JSON_EXTRACT_SCALAR(json_obj, '$.url') AS url,
            SAFE_CAST(JSON_EXTRACT_SCALAR(json_obj, '$.parent') AS INT64) AS parent_id,
            SAFE_CAST(JSON_EXTRACT_SCALAR(json_obj, '$.score') AS INT64) AS score,
            SAFE_CAST(JSON_EXTRACT_SCALAR(json_obj, '$.descendants') AS INT64) AS descendants,
            '{ingest_date}' as ingest_date_str,
            _FILE_NAME as source_file
        FROM parsed_json;
        """

        print(f"Processing date {ingest_date}...")
        job = bq_client.query(bq_script)
        job.result()
        print(f"Completed processing {ingest_date}.")

        # Update checkpoint
        blobs = list(
            storage_client.list_blobs(
                bronze_bucket, prefix=f"bronze/{ingest_date_path}/"
            )
        )
        checkpoint_data[ingest_date] = {
            "file_count": len(blobs),
            "total_bytes": sum(blob.size for blob in blobs),
        }


def save_checkpoint(
    checkpoint_data: Dict[str, Any], tmp_file_path: str, blob: storage.Blob
) -> None:
    with open(tmp_file_path, "w") as f:
        json.dump(checkpoint_data, f)
    blob.upload_from_filename(tmp_file_path)


def main():
    tf_dir = Path(__file__).parent.parent / "infra" / "terraform"
    outputs = get_terraform_outputs(tf_dir)

    GCP_PROJECT_ID = outputs["project_id"]
    BRONZE_BUCKET = outputs["bronze_bucket_name"]
    SILVER_BUCKET = outputs["silver_bucket_name"]
    BRONZE_DATASET_ID = outputs["bronze_dataset_id"]

    checkpoint_data, tmp_checkpoint_path, checkpoint_blob = load_checkpoint(
        SILVER_BUCKET, "silver/checkpoints/bronze_file_state.json"
    )
    dates_to_process = get_dates_to_process(BRONZE_BUCKET, checkpoint_data)

    if not dates_to_process:
        print("No new or updated data to process. Exiting.")
        return

    process_dates_in_bq(
        dates_to_process,
        GCP_PROJECT_ID,
        BRONZE_DATASET_ID,
        BRONZE_BUCKET,
        SILVER_BUCKET,
        checkpoint_data,
    )
    save_checkpoint(checkpoint_data, tmp_checkpoint_path, checkpoint_blob)
    print("All unprocessed dates have been processed.")


if __name__ == "__main__":
    main()
