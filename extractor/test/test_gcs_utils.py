import io
import time
from extractor.src.gcs_utils import upload_to_gcs

BUCKET_NAME = "hn-dev-bronze-bucket"


def test_atomic_upload():
    """
    A simple test to verify the atomic upload functionality.
    """
    print("--- Starting atomic upload test ---")

    # Create a fake data stream
    fake_data = '{"id": 1, "name": "test_item_1"}\n{"id": 2, "name": "test_item_2"}\n'
    data_stream = io.BytesIO(fake_data.encode("utf-8"))

    # Create a fake manifest
    manifest = {"source": "test_script", "item_count": 2}

    # 2. Define paths
    # Use timestamp to make each run unique
    timestamp = int(time.time())
    blob_name = f"bronze/test_run/{timestamp}/test_data.jsonl"  # No .gz because data is not compressed

    # 3. Call the function
    try:
        upload_to_gcs(
            bucket_name=BUCKET_NAME,
            blob_name=blob_name,
            data_stream=data_stream,
            manifest=manifest,
        )
        print("\n--- Test finished successfully! ---")
        print("Please check your GCS bucket for the following files:")
        print(f"  - gs://{BUCKET_NAME}/{blob_name}")
        print(f"  - gs://{BUCKET_NAME}/{blob_name.replace('.jsonl', '_manifest.json')}")
        print(f"  - gs://{BUCKET_NAME}/bronze/test_run/{timestamp}/_SUCCESS")
        print("Also, ensure the '_inflight' directory is empty.")

    except Exception as e:
        print(f"\n--- Test failed with an error: {e} ---")


if __name__ == "__main__":
    test_atomic_upload()
