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
    "Exception tuy chinh cho cac loi API khong nen retry (vd: 4xx)"

    pass


class TemporaryAPIError(Exception):
    "Exception tuy chinh cho cac loi API co the retry (vd: 5xx)"

    pass


@retry(
    retry=retry_if_exception_type(TemporaryAPIError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=60),
)
def fetch_item(item_id: int) -> Optional[Dict[str, Any]]:
    """
    Lay thong tin cua mot item tu Hacker News API.
    Ham duoc retry neu gap loi tam thoi (5xx).

    Args:
        item_id (int): ID cua item can lay.
    Returns:
        Optional[Dict[str, Any]]: Du lieu item neu thanh cong, None neu item khong ton tai.
    Raises:
        APIError: Neu gap loi khong nen retry (4xx).
        TemporaryAPIError: Neu gap loi co the retry (5xx).
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
    Lay ID cua item lon nhat tu Hacker News API.
    Returns:
        int: ID cua item lon nhat.
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
    Lay mot story va tat ca comment cua no tu Hacker News API.
    Su dung ThreadPoolExecutor de lay cac comment dong thoi.

    Args:
        story_id (int): ID cua story can lay.
    Returns:
        List[Dict[str, Any]]: Danh sach story va cac comment lien quan.
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
            time.sleep(0.1)  # De tranh qua tai API

    return all_items


def fetch_items_concurrently(
    start_id: int, end_id: int, max_workers: int = 20
) -> List[Optional[Dict[str, Any]]]:
    """
    Lay nhieu item tu Hacker News API mot cach dong thoi su dung ThreadPoolExecutor.

    Args:
        start_id (int): ID bat dau.
        end_id (int): ID ket thuc.
        max_workers (int): So luong thread toi da.
    Returns:
        List[Optional[Dict[str, Any]]]: Danh sach cac item duoc lay.
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
