# extractor/src/gcs_utils.py
import json
from google.cloud import storage
from google.api_core import exceptions as gcs_exceptions


def upload_to_gcs(bucket_name: str, blob_name: str, data_stream, manifest: dict):
    """
    Upload du lieu tu stream len Google Cloud Storage (GCS) va luu manifest.
    Args:
        bucket_name (str): Ten cua GCS bucket.
        blob_name (str): Ten cua dich cuoi cung cua file trong bucket.
        data_stream: Stream chua du lieu can upload.
        manifest (dict): Metadata cua file de luu o manifest.
    Raises:
        gcs_exceptions.GoogleAPIError: Neu co loi khi upload len GCS.
    """
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)

        final_blob_name = blob_name
        temp_blob_name = f"_inflight/{blob_name}"

        # Upload file tam thoi
        print(f"Uploading to temporary location: gs://{bucket_name}/{temp_blob_name}")
        temp_blob = bucket.blob(temp_blob_name)
        temp_blob.upload_from_file(data_stream, content_type="application/gzip")
        print("Upload to temporary location completed.")

        # Chuyen file tu tam thoi sang vi tri cuoi cung
        print(f"Copying to final location: gs://{bucket_name}/{final_blob_name}")
        bucket.copy_blob(temp_blob, bucket, final_blob_name)
        print("Copy to final location completed.")

        # Tao va upload manifest
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
        # Xoa file tam thoi neu con ton tai
        try:
            if bucket.blob(temp_blob_name).exists():
                bucket.blob(temp_blob_name).delete()
                print(f"Temporary blob gs://{bucket_name}/{temp_blob_name} deleted.")
        except Exception as cleanup_err:
            print(f"Error cleaning up temporary blob: {cleanup_err}")


def read_checkpoint(bucket_name: str, checkpoint_path: str) -> int:
    """
    Doc checkpoint tu GCS de biet duoc item_id bat dau.
    Args:
        bucket_name (str): Ten cua GCS bucket.
        checkpoint_path (str): Duong dan den file checkpoint trong bucket.
    Returns:
        int: item_id bat dau. Neu khong co checkpoint, tra ve 0.
    Raises:
        gcs_exceptions.GoogleAPIError: Neu co loi khi doc tu GCS.
    """
    try:
        storage_client = storage.Client()
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


def write_checkpoint(bucket_name: str, checkpoint_path: str, last_id: int):
    """
    Ghi checkpoint len GCS de luu item_id da xu ly cuoi cung.
    Args:
        bucket_name (str): Ten cua GCS bucket.
        checkpoint_path (str): Duong dan den file checkpoint trong bucket.
        last_id (int): item_id da xu ly cuoi cung.
    Raises:
        gcs_exceptions.GoogleAPIError: Neu co loi khi ghi len GCS.
    """
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(checkpoint_path)
        blob.upload_from_string(str(last_id), content_type="text/plain")
        print(
            f"Checkpoint gs://{bucket_name}/{checkpoint_path} updated to item_id {last_id}."
        )

    except gcs_exceptions.GoogleAPICallError as gcs_err:
        print(f"Error writing checkpoint to GCS: {gcs_err}")
