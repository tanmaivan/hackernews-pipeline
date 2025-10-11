import unittest
import json
import gzip
import io
from extractor.src.processing import process_items_to_gzipped_ndjson


class TestProcessing(unittest.TestCase):

    def test_process_items_successfully(self):
        """
        Test the happy path where:
        - Data is correctly compressed.
        - NDJSON format is correct.
        - Item count is accurate.
        - Stream is reset to the beginning.
        """
        sample_items = [
            {"id": 1, "type": "story", "by": "userA"},
            {"id": 2, "type": "comment", "parent": 1, "text": "A comment"},
        ]

        gzipped_stream, count = process_items_to_gzipped_ndjson(sample_items)

        # Test the return types and count
        self.assertIsInstance(
            gzipped_stream, io.BytesIO, "The result must be a BytesIO stream"
        )
        self.assertEqual(count, 2, "The number of processed items must be 2")

        # Test the stream position is reset to the beginning
        self.assertEqual(
            gzipped_stream.tell(),
            0,
            "Stream must be seeked to the beginning to be read",
        )

        compressed_data = gzipped_stream.read()
        decompressed_data = gzip.decompress(compressed_data)

        result_lines = decompressed_data.decode("utf-8").strip().split("\n")
        result_items = [json.loads(line) for line in result_lines]

        self.assertEqual(len(result_items), 2)
        self.assertIn(sample_items[0], result_items)
        self.assertIn(sample_items[1], result_items)

    def test_empty_list_input(self):
        """
        Test the case where the input is an empty list. The function should handle it gracefully, returning an empty stream and count = 0.
        """
        # 1. Input
        empty_items = []

        # 2. Action
        gzipped_stream, count = process_items_to_gzipped_ndjson(empty_items)

        # 3. Assertions
        self.assertEqual(count, 0, "Number of processed items must be 0")

        decompressed_data = gzip.decompress(gzipped_stream.read())
        self.assertEqual(
            decompressed_data,
            b"",
            "Content of the stream after decompression must be empty",
        )

    def test_unserializable_item_is_skipped(self):
        """
        Test the case where one item in the list cannot be serialized to JSON. The function should skip the erroneous item and process the rest.
        """
        items_with_error = [
            {"id": 1, "valid": True},
            {"id": 2, "invalid_data": {1, 2, 3}},
            {"id": 3, "valid": True},
        ]

        gzipped_stream, count = process_items_to_gzipped_ndjson(items_with_error)

        self.assertEqual(count, 2, "Only 2 items should be processed successfully")

        decompressed_data = gzip.decompress(gzipped_stream.read()).decode("utf-8")
        result_items = [
            json.loads(line) for line in decompressed_data.strip().split("\n")
        ]

        ids_in_result = {item["id"] for item in result_items}
        self.assertIn(1, ids_in_result)
        self.assertIn(3, ids_in_result)
        self.assertNotIn(2, ids_in_result, "Invalid item should not be in the output")


if __name__ == "__main__":
    unittest.main()
