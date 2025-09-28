# extractor/src/main.py
from datetime import datetime
from extractor.src.hn_client import get_max_item_id, fetch_items_concurrently
from extractor.src.processing import process_items_to_gzipped_ndjson
from extractor.src.gcs_utils import upload_to_gcs, read_checkpoint, write_checkpoint
from extractor.src.config import BUCKET_NAME
import sys
import time

CHUNK_SIZE = 10000  # So luong item lay moi lan
TOTAL_ITEMS = 100000  # Tong so item can lay


def main():
    total_pipeline_start_time = time.time()
    print(
        f"--- Starting HackerNews Extractor (Limited Backfill: {TOTAL_ITEMS} items) ---"
    )

    # Step 0: Read the last checkpoint
    checkpoint_path = "checkpoints/last_item_id.txt"
    last_processed_id = read_checkpoint(BUCKET_NAME, checkpoint_path)

    end_id = get_max_item_id()
    start_id = max(last_processed_id + 1, end_id - TOTAL_ITEMS + 1)

    if start_id > end_id:
        print("No new items to process. Exiting.")
        return

    print(f"Processing items from ID {start_id} to {end_id}...")
    print(f"Processing in chunks of {CHUNK_SIZE} items.")

    for chunk_start_id in range(start_id, end_id + 1, CHUNK_SIZE):
        chunk_start_time = time.time()
        chunk_end_id = min(chunk_start_id + CHUNK_SIZE - 1, end_id)
        print("\n" + "=" * 50)
        print(f"Processing chunk: ID {chunk_start_id} to {chunk_end_id}")
        print("=" * 50)

        # Step 1: Fetch items concurrently
        fetch_start_time = time.time()
        print("\nStep 1: Fetching items...")
        raw_items_chunk = fetch_items_concurrently(chunk_start_id, chunk_end_id)
        fetch_duration = time.time() - fetch_start_time
        print(
            f"-> Fetched {len(raw_items_chunk)} items in {fetch_duration:.2f} seconds."
        )

        if not raw_items_chunk:
            print("Fetched 0 items in this chunk. Skipping to next chunk.")
            write_checkpoint(BUCKET_NAME, checkpoint_path, chunk_end_id)
            continue

        # Step 2: Process items into gzipped NDJSON
        process_start_time = time.time()
        print("\nStep 2: Processing items into gzipped NDJSON...")
        compressed_data_stream, item_count = process_items_to_gzipped_ndjson(
            raw_items_chunk
        )
        process_duration = time.time() - process_start_time
        print(
            f"-> Processed {item_count} items into gzipped NDJSON in {process_duration:.2f} seconds."
        )

        # Step 3: Upload to GCS atomically
        upload_start_time = time.time()
        print("\nStep 3: Uploading to GCS...")
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

        upload_to_gcs(BUCKET_NAME, blob_name, compressed_data_stream, manifest)
        upload_duration = time.time() - upload_start_time
        print(f"-> Uploaded to GCS in {upload_duration:.2f} seconds.")

        # Step 4: Update checkpoint
        print("\nStep 4: Updating checkpoint...")
        write_checkpoint(BUCKET_NAME, checkpoint_path, chunk_end_id)

        chunk_duration = time.time() - chunk_start_time

        print(
            f"\n--- Successfully processed chunk up to ID {chunk_end_id} in {chunk_duration:.2f} seconds.---"
        )
        sys.stdout.flush()

    total_pipeline_duration = time.time() - total_pipeline_start_time
    print("\n--- Hacker News Extractor Pipeline finished successfully! ---")
    print(f"--- Total pipeline duration: {total_pipeline_duration:.2f} seconds.")
    print("------------------------------------------------------------")


if __name__ == "__main__":
    main()
