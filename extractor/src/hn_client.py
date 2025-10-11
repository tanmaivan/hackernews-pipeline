# extractor/src/hn_client.py
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Dict, Any, List
from tqdm import tqdm

BASE_URL = "https://hacker-news.firebaseio.com/v0/"


class APIError(Exception):
    "Exception for non-retryable API errors (e.g., 4xx)"

    pass


class TemporaryAPIError(Exception):
    "Exception for temporary API errors (e.g., 5xx)"

    pass


@retry(
    retry=retry_if_exception_type(TemporaryAPIError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=60),
)
def fetch_item(item_id: int) -> Optional[Dict[str, Any]]:
    """
    Fetch an item from the Hacker News API. Retries on temporary errors (5xx).
    Args:
        item_id (int): The ID of the item to fetch.
    Returns:
        Optional[Dict[str, Any]]: The item data if successful, None if the item does not exist.
    Raises:
        APIError: If a non-retryable error occurs (4xx).
        TemporaryAPIError: If a retryable error occurs (5xx).
    """
    url = f"{BASE_URL}/item/{item_id}.json"

    try:
        response = requests.get(url, timeout=10)

        response.raise_for_status()

        if response.text == "null":
            return None

        return response.json()

    except requests.exceptions.HTTPError as http_err:
        if 400 <= response.status_code < 500:
            raise APIError(
                f"Client error {response.status_code} for item {item_id}"
            ) from http_err
        elif 500 <= response.status_code < 600:
            raise TemporaryAPIError(
                f"Server error {response.status_code} for item {item_id}"
            ) from http_err
        else:
            raise

    except (
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
    ) as conn_err:
        raise TemporaryAPIError(f"Connection error for item {item_id}") from conn_err


def get_max_item_id() -> int:
    """
    Fetches the maximum item ID from the Hacker News API.
    Returns:
        int: The maximum item ID.
    """
    url = f"{BASE_URL}/maxitem.json"

    try:
        response = requests.get(url, timeout=10)

        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestsException as req_err:
        if response.status_code >= 500:
            raise TemporaryAPIError(
                "Server error while fetching max item ID"
            ) from req_err
        else:
            raise APIError("Client error while fetching max item ID") from req_err


def fetch_story_with_comments(story_id: int) -> List[Dict[str, Any]]:
    """
    Fetch a story and all its comments from the Hacker News API.
    Uses ThreadPoolExecutor to fetch comments concurrently.
    Args:
        story_id (int): The ID of the story to fetch.
    Returns:
        List[Dict[str, Any]]: A list containing the story and all related comments.
    """

    all_items = []
    root_story = fetch_item(story_id)
    if not root_story or root_story.get("type") != "story":
        return all_items

    all_items.append(root_story)

    comment_ids = root_story.get("kids", [])

    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_id = {executor.submit(fetch_item, cid): cid for cid in comment_ids}

        while future_to_id:
            new_futures = {}
            for future in as_completed(future_to_id):
                item_id = future_to_id[future]
                try:
                    comment = future.result()
                    if comment:
                        all_items.append(comment)
                        if "kids" in comment:
                            for kid_id in comment["kids"]:
                                new_futures[executor.submit(fetch_item, kid_id)] = (
                                    kid_id
                                )
                except Exception as e:
                    print(f"Error fetching comment {item_id}: {e}")
            future_to_id = new_futures
            time.sleep(0.1)  # to avoid overwhelming the API

    return all_items


def fetch_items_concurrently(
    start_id: int, end_id: int, max_workers: int = 20
) -> List[Optional[Dict[str, Any]]]:
    """
    Fetch multiple items from the Hacker News API concurrently using ThreadPoolExecutor.
    Args:
        start_id (int): The starting item ID.
        end_id (int): The ending item ID.
        max_workers (int): The maximum number of threads to use.
    Returns:
        List[Optional[Dict[str, Any]]]: A list of fetched items.
    """
    print(f"Fetching items from {start_id} to {end_id} with {max_workers} workers...")
    items = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_id = {
            executor.submit(fetch_item, item_id): item_id
            for item_id in range(start_id, end_id + 1)
        }

        try:
            futures = tqdm(
                as_completed(future_to_id),
                total=len(future_to_id),
                desc="Fetching items",
            )
        except ImportError:
            futures = as_completed(future_to_id)

        for future in futures:
            item_id = future_to_id[future]
            try:
                item = future.result()
                items.append(item)
            except Exception as e:
                print(f"Error fetching item {item_id}: {e}")

    return items
