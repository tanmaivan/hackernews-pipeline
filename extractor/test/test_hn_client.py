import json
from extractor.src.hn_client import (
    fetch_item,
    get_max_item_id,
    fetch_story_with_comments,
    fetch_items_concurrently,
)


def print_json(data):
    """Hàm helper để in JSON cho đẹp."""
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    print("--- 1. Testing get_max_item_id ---")
    try:
        max_id = get_max_item_id()
        print(f"Current Max Item ID: {max_id}")
    except Exception as e:
        print(f"Error: {e}")

    print("\n" + "=" * 40 + "\n")

    # --- Test fetch_item ---
    # ID 8863 là bài "My YC app: Dropbox - Throw away your USB drive"
    story_id_to_test = 8863
    print(f"--- 2. Testing fetch_item for a valid story (ID: {story_id_to_test}) ---")
    try:
        item = fetch_item(story_id_to_test)
        if item:
            print_json(item)
        else:
            print("Item not found or is null.")
    except Exception as e:
        print(f"Error: {e}")

    print("\n" + "=" * 40 + "\n")

    # --- Test với ID không tồn tại (một số rất lớn) ---
    invalid_id = 999999999
    print(f"--- 3. Testing fetch_item for a non-existent item (ID: {invalid_id}) ---")
    try:
        item = fetch_item(invalid_id)
        if item:
            print("Error: Should not have found an item!")
            print_json(item)
        else:
            print(f"Correctly returned None for non-existent ID {invalid_id}.")
    except Exception as e:
        # Ta kỳ vọng nó sẽ retry vài lần và cuối cùng ném ra lỗi hoặc trả về None
        print(f"Handled error as expected: {e}")

    print("\n" + "=" * 40 + "\n")

    # --- Test fetch_story_with_comments (Lưu ý: sẽ gọi nhiều API) ---
    # ID 8863 là một story kinh điển về Dropbox, có rất nhiều comments.
    # Sử dụng ID này để đảm bảo test đúng chức năng.
    story_with_comments_id = 8863
    print(
        f"--- 4. Testing fetch_story_with_comments (ID: {story_with_comments_id}) ---"
    )
    try:
        all_items = fetch_story_with_comments(story_with_comments_id)

        # Thêm một bước kiểm tra để tránh lỗi
        if all_items:
            print(
                f"Fetched story and a total of {len(all_items) - 1} child items (comments)."
            )
            print("Sample item (the story itself):")
            # In ra story gốc
            print_json(all_items[0])
        else:
            print(
                "Function returned an empty list. The ID might not be a story or does not exist."
            )

    except Exception as e:
        print(f"An error occurred: {e}")

    print("\n" + "=" * 40 + "\n")
    # --- Test fetch_items_concurrently ---
    print("--- 5. Testing fetch_items_concurrently (IDs: 8860 to 8870) ---")
    try:
        items = fetch_items_concurrently(8860, 8870, max_workers=5)
        fetched_count = sum(1 for item in items if item is not None)
        print(f"Fetched {fetched_count} items out of 11 requested.")
        print("Sample fetched items:")
        for item in items:
            if item:
                print_json(item)
    except Exception as e:
        print(f"Error: {e}")
