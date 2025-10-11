# extractor/src/processing.py
import io
import gzip
import json
from typing import List, Dict, Any, Tuple


def process_items_to_gzipped_ndjson(
    items: List[Dict[str, Any]],
) -> Tuple[io.BytesIO, int]:
    """
    Convert a list of items into a Gzip-compressed NDJSON file directly in memory.
    Args:
        items: List of items (as dictionaries).
    Returns:
        A tuple containing:
        - io.BytesIO: In-memory stream containing the compressed data.
        - int: Count of items successfully processed.
    """
    processed_count = 0
    in_memory_buffer = io.BytesIO()

    gz_file = gzip.GzipFile(fileobj=in_memory_buffer, mode="wb")

    for item in items:
        if item:
            try:
                line = json.dumps(item) + "\n"
                gz_file.write(line.encode("utf-8"))
                processed_count += 1
            except (TypeError, OverflowError) as e:
                item_id = item.get("id", "N/A")
                print(
                    f"Warning: Could not serialize item {item_id}. Skipping. Reason: {e}"
                )

    # We must close the GzipFile to ensure all compressed data is flushed to the underlying buffer.
    gz_file.close()

    # Now, in_memory_buffer is still valid and not closed.
    # We can safely seek it back to the beginning.
    in_memory_buffer.seek(0)

    print(f"Processed and compressed {processed_count} items into memory.")
    return in_memory_buffer, processed_count
