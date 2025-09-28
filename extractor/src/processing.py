# extractor/src/processing.py
import io
import gzip
import json
from typing import List, Dict, Any, Tuple


def process_items_to_gzipped_ndjson(
    items: List[Dict[str, Any]],
) -> Tuple[io.BytesIO, int]:
    """
    Chuyển đổi một danh sách các item thành một file NDJSON nén bằng Gzip
    trực tiếp trong bộ nhớ.

    Args:
        items: Danh sách các item (dưới dạng dictionary).

    Returns:
        Một tuple chứa:
        - io.BytesIO: Stream trong bộ nhớ chứa dữ liệu đã nén.
        - int: Số lượng item đã được xử lý thành công.
    """
    processed_count = 0
    in_memory_buffer = io.BytesIO()

    # Cách tiếp cận an toàn hơn:
    # Chúng ta tự quản lý việc mở và đóng GzipFile,
    # đảm bảo buffer gốc không bị đóng theo.
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

    # Rất quan trọng: Phải đóng GzipFile để đảm bảo tất cả dữ liệu nén
    # được ghi hết vào buffer bên dưới.
    gz_file.close()

    # Bây giờ, in_memory_buffer vẫn hoàn toàn hợp lệ và chưa bị đóng.
    # Chúng ta có thể seek nó về đầu một cách an toàn.
    in_memory_buffer.seek(0)

    print(f"Processed and compressed {processed_count} items into memory.")
    return in_memory_buffer, processed_count
