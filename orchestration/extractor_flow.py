# orchestration/extractor_flow.py
from datetime import datetime
from extractor.src.hn_client import get_max_item_id, fetch_items_concurrently
from extractor.src.processing import process_items_to_gzipped_ndjson
from extractor.src.gcs_utils import upload_to_gcs, read_checkpoint, write_checkpoint
from prefect.variables import Variable
import time
from prefect import flow, task
from prefect_gcp import GcpCredentials


CHUNK_SIZE = 10000  # number of items to process in each chunk
TOTAL_ITEMS = 100000  # total number of items to backfill
BUCKET_NAME = Variable.get("bronze_bucket")


@task(log_prints=True, retries=3, retry_delay_seconds=10)
def fetch_data_task(start_id, end_id):
    print(f"Fetching items from ID {start_id} to {end_id}...")
    return fetch_items_concurrently(start_id, end_id)


@task(log_prints=True)
def process_data_task(raw_items):
    print(f"Processing {len(raw_items)} items into gzipped NDJSON...")
    return process_items_to_gzipped_ndjson(raw_items)


@task(log_prints=True)
def upload_data_task(gcs_info, compressed_stream, item_count, gcp_credentials_block):
    print(f"Uploading {item_count} items to GCS...")
    upload_to_gcs(
        gcs_info["bucket_name"],
        gcs_info["blob_name"],
        compressed_stream,
        gcs_info["manifest"],
        gcp_credentials_block,
    )


@flow(name="HackerNews Bronze Ingestion", log_prints=True)
def extractor_flow(chunk_size: int = 10000, total_items: int = 100000):
    """
    Prefect flow to extract Hacker News items and upload them to GCS in chunks.
    Args:
        chunk_size (int): Number of items to process in each chunk.
        total_items (int): Total number of items to backfill.
    1. Reads the last processed item ID from a checkpoint in GCS.
    2. Determines the range of item IDs to process based on the last checkpoint and total_items.
    3. For each chunk of item IDs:
        a. Fetches items concurrently using the Hacker News API.
        b. Processes the fetched items into gzipped NDJSON format.
        c. Uploads the processed data to GCS with a manifest.
        d. Updates the checkpoint in GCS with the last processed item ID.
    Returns:
        None
    """
    gcp_credentials_block = GcpCredentials.load("gcp-creds")

    # checkpoint_path = "checkpoints/last_item_id.txt"
    checkpoint_path = "checkpoints/last_item_id.txt"
    last_processed_id = read_checkpoint(
        BUCKET_NAME, checkpoint_path, gcp_credentials_block
    )

    end_id = get_max_item_id()
    start_id = max(last_processed_id + 1, end_id - total_items + 1)

    if start_id > end_id:
        print("No new items to process. Exiting.")
        return

    print(
        f"Processing items from ID {start_id} to {end_id} in chunks of {chunk_size} items."
    )

    for chunk_start_id in range(start_id, end_id + 1, chunk_size):
        chunk_start_time = time.time()
        chunk_end_id = min(chunk_start_id + chunk_size - 1, end_id)
        print("\n" + "=" * 50)
        print(f"Processing chunk: ID {chunk_start_id} to {chunk_end_id}")
        print("=" * 50)

        # Step 1: Fetch items concurrently
        raw_items_chunk = fetch_data_task(chunk_start_id, chunk_end_id)

        if not raw_items_chunk:
            print("Fetched 0 items in this chunk. Skipping to next chunk.")
            write_checkpoint(
                BUCKET_NAME, checkpoint_path, chunk_end_id, gcp_credentials_block
            )
            continue

        # Step 2: Process items into gzipped NDJSON
        compressed_data_stream, item_count = process_data_task(raw_items_chunk)

        # Step 3: Upload to GCS atomically
        now = datetime.utcnow()
        file_timestamp = now.strftime("%Y%m%d_%H%M%S")
        blob_name = f"bronze/{now.strftime('%Y/%m/%d')}/hn_items_{chunk_start_id}_{chunk_end_id}_{file_timestamp}.jsonl.gz"

        manifest = {
            "timestamp": now.isoformat(),
            "source": "Hacker News API",
            "file_format": "NDJSON_GZ",
            "item_count": item_count,
            "id_range": {"start": chunk_start_id, "end": chunk_end_id},
            "gcs_path": f"gs://{BUCKET_NAME}/{blob_name}",
        }

        gcs_info = {
            "bucket_name": BUCKET_NAME,
            "blob_name": blob_name,
            "manifest": manifest,
        }

        upload_data_task(
            gcs_info, compressed_data_stream, item_count, gcp_credentials_block
        )

        # Step 4: Update checkpoint
        print("\nStep 4: Updating checkpoint...")
        write_checkpoint(
            BUCKET_NAME, checkpoint_path, chunk_end_id, gcp_credentials_block
        )

        chunk_duration = time.time() - chunk_start_time

        print(
            f"\n--- Successfully processed chunk up to ID {chunk_end_id} in {chunk_duration:.2f} seconds.---"
        )


if __name__ == "__main__":
    extractor_flow(chunk_size=CHUNK_SIZE, total_items=TOTAL_ITEMS)
