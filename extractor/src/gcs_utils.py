# extractor/src/gcs_utils.py
import json
from google.cloud import storage, bigquery
from google.api_core import exceptions as gcs_exceptions
from google.oauth2.service_account import Credentials


def get_gcs_client(gcp_credentials_block):
    """
    Create a Google Cloud Storage (GCS) client from a Prefect GCP Credentials block.
    Args:
        gcp_credentials_block: Prefect GCP Credentials block containing authentication info.
    Returns:
        storage.Client: GCS client.
    """
    creds_dict = gcp_credentials_block.service_account_info.get_secret_value()
    credentials = Credentials.from_service_account_info(creds_dict)

    return storage.Client(credentials=credentials)


def get_bq_client(gcp_credentials_block):
    """
    Creates a Google BigQuery client from a Prefect GCP Credentials block.
    Args:
        gcp_credentials_block: Prefect GCP Credentials block containing authentication info.
    Returns:
        bigquery.Client: BigQuery client.
    """
    creds_dict = gcp_credentials_block.service_account_info.get_secret_value()
    credentials = Credentials.from_service_account_info(creds_dict)

    return bigquery.Client(credentials=credentials)


def upload_to_gcs(
    bucket_name: str, blob_name: str, data_stream, manifest: dict, gcp_credentials_block
):
    """
    Upload data from a stream to Google Cloud Storage (GCS) and save a manifest.
    Args:
        bucket_name (str): Name of the GCS bucket.
        blob_name (str): Final destination name of the file in the bucket.
        data_stream: Stream containing the data to upload.
        manifest (dict): Metadata of the file to save in the manifest.
        gcp_credentials_block: Prefect GCP Credentials block containing authentication info.
    Raises:
        gcs_exceptions.GoogleAPIError: If there is an error uploading to GCS.
    """
    try:
        storage_client = get_gcs_client(gcp_credentials_block)
        bucket = storage_client.bucket(bucket_name)

        final_blob_name = blob_name
        temp_blob_name = f"_inflight/{blob_name}"

        # Upload to temporary location
        print(f"Uploading to temporary location: gs://{bucket_name}/{temp_blob_name}")
        temp_blob = bucket.blob(temp_blob_name)
        temp_blob.upload_from_file(data_stream, content_type="application/gzip")
        print("Upload to temporary location completed.")

        # Copy to final location
        print(f"Copying to final location: gs://{bucket_name}/{final_blob_name}")
        bucket.copy_blob(temp_blob, bucket, final_blob_name)
        print("Copy to final location completed.")

        # Create and upload manifest
        manifest_blob_name = final_blob_name.replace(".jsonl.gz", "_manifest.json")
        manifest_blob = bucket.blob(manifest_blob_name)
        manifest_blob.upload_from_string(
            json.dumps(manifest), content_type="application/json"
        )

        # file _SUCCESS
        success_blob_name = f"{'/'.join(final_blob_name.split('/')[:-1])}/_SUCCESS"
        success_blob = bucket.blob(success_blob_name)
        success_blob.upload_from_string("", content_type="text/plain")

        print(f"Upload manifest to: gs://{bucket_name}/{manifest_blob_name} completed.")
        print(f"Upload _SUCCESS to: gs://{bucket_name}/{success_blob_name} completed.")

    except gcs_exceptions.GoogleAPICallError as gcs_err:
        print(f"Error uploading to GCS: {gcs_err}")
        raise

    finally:
        # Delete temporary file if it exists
        try:
            if bucket.blob(temp_blob_name).exists():
                bucket.blob(temp_blob_name).delete()
                print(f"Temporary blob gs://{bucket_name}/{temp_blob_name} deleted.")
        except Exception as cleanup_err:
            print(f"Error cleaning up temporary blob: {cleanup_err}")


def read_checkpoint(
    bucket_name: str, checkpoint_path: str, gcp_credentials_block
) -> int:
    """
    Read checkpoint from GCS to determine the starting item_id.
    Args:
        bucket_name (str): Name of the GCS bucket.
        checkpoint_path (str): Path to the checkpoint file in the bucket.
        gcp_credentials_block: Prefect GCP Credentials block containing authentication info.
    Returns:
        int: Starting item_id. If no checkpoint exists, returns 0.
    Raises:
        gcs_exceptions.GoogleAPIError: If there is an error reading from GCS.
    """
    try:
        storage_client = get_gcs_client(gcp_credentials_block)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(checkpoint_path)
        if not blob.exists():
            print(
                f"Checkpoint file gs://{bucket_name}/{checkpoint_path} does not exist. Starting from item_id 0."
            )
            return 0
        last_id_str = blob.download_as_string().decode("utf-8")
        return int(last_id_str.strip())

    except gcs_exceptions.NotFound:
        print(
            f"Checkpoint file gs://{bucket_name}/{checkpoint_path} not found. Starting from item_id 0."
        )
        return 0


def write_checkpoint(
    bucket_name: str, checkpoint_path: str, last_id: int, gcp_credentials_block
):
    """
    Write checkpoint to GCS to save the last processed item_id.
    Args:
        bucket_name (str): Name of the GCS bucket.
        checkpoint_path (str): Path to the checkpoint file in the bucket.
        last_id (int): Last processed item_id.
        gcp_credentials_block: Prefect GCP Credentials block containing authentication info.
    Raises:
        gcs_exceptions.GoogleAPIError: If there is an error writing to GCS.
    """
    try:
        storage_client = get_gcs_client(gcp_credentials_block)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(checkpoint_path)
        blob.upload_from_string(str(last_id), content_type="text/plain")
        print(
            f"Checkpoint gs://{bucket_name}/{checkpoint_path} updated to item_id {last_id}."
        )

    except gcs_exceptions.GoogleAPICallError as gcs_err:
        print(f"Error writing checkpoint to GCS: {gcs_err}")
