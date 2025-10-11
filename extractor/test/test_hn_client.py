import json
from extractor.src.hn_client import (
    fetch_item,
    get_max_item_id,
    fetch_story_with_comments,
    fetch_items_concurrently,
)


def print_json(data):
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

    # --- Test fetch_item with a non-existent ID (a very large number) ---
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
        print(f"Handled error as expected: {e}")

    print("\n" + "=" * 40 + "\n")

    # --- Test fetch_story_with_comments (Note: will call many APIs) ---
    # ID 8863 is a classic story about Dropbox with many comments.
    # Use this ID to ensure the function is tested properly.
    story_with_comments_id = 8863
    print(
        f"--- 4. Testing fetch_story_with_comments (ID: {story_with_comments_id}) ---"
    )
    try:
        all_items = fetch_story_with_comments(story_with_comments_id)

        if all_items:
            print(
                f"Fetched story and a total of {len(all_items) - 1} child items (comments)."
            )
            print("Sample item (the story itself):")
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
