import unittest
import json
import gzip
import io

# Import àm mà chúng ta muốn test từ thư mục src
from extractor.src.processing import process_items_to_gzipped_ndjson


# Tạo một lớp test kế thừa từ unittest.TestCase
class TestProcessing(unittest.TestCase):

    def test_process_items_successfully(self):
        """
        Kiểm tra trường hợp hoạt động bình thường:
        - Dữ liệu có được nén đúng không?
        - Định dạng NDJSON có chính xác không?
        - Số lượng item có đúng không?
        - Stream có được reset về vị trí đầu không?
        """
        # 1. Chuẩn bị dữ liệu đầu vào (Input)
        sample_items = [
            {"id": 1, "type": "story", "by": "userA"},
            {"id": 2, "type": "comment", "parent": 1, "text": "A comment"},
        ]

        # 2. Gọi hàm cần test (Action)
        gzipped_stream, count = process_items_to_gzipped_ndjson(sample_items)

        # 3. Kiểm tra kết quả (Assertions)

        # a) Kiểm tra kiểu dữ liệu trả về và số lượng
        self.assertIsInstance(
            gzipped_stream, io.BytesIO, "Kết quả trả về phải là một BytesIO stream"
        )
        self.assertEqual(count, 2, "Số lượng item xử lý phải là 2")

        # b) Kiểm tra con trỏ của stream đã được đưa về đầu (vị trí 0)
        self.assertEqual(
            gzipped_stream.tell(),
            0,
            "Stream phải được seek về vị trí đầu tiên để có thể đọc",
        )

        # c) Đọc và giải nén stream để kiểm tra nội dung
        compressed_data = gzipped_stream.read()
        decompressed_data = gzip.decompress(compressed_data)

        # d) Chuyển dữ liệu đã giải nén thành chuỗi và so sánh
        # Chú ý: json.dumps không đảm bảo thứ tự key, nên ta cần parse lại để so sánh
        result_lines = decompressed_data.decode("utf-8").strip().split("\n")
        result_items = [json.loads(line) for line in result_lines]

        self.assertEqual(len(result_items), 2)
        self.assertIn(sample_items[0], result_items)
        self.assertIn(sample_items[1], result_items)

    def test_empty_list_input(self):
        """
        Kiểm tra trường hợp đầu vào là một danh sách rỗng.
        Hàm nên xử lý một cách an toàn và trả về stream rỗng, count = 0.
        """
        # 1. Input
        empty_items = []

        # 2. Action
        gzipped_stream, count = process_items_to_gzipped_ndjson(empty_items)

        # 3. Assertions
        self.assertEqual(count, 0, "Số lượng item xử lý phải là 0")

        # Giải nén và kiểm tra nội dung
        decompressed_data = gzip.decompress(gzipped_stream.read())
        self.assertEqual(
            decompressed_data, b"", "Nội dung của stream sau khi giải nén phải là rỗng"
        )

    def test_unserializable_item_is_skipped(self):
        """
        Kiểm tra trường hợp một item trong danh sách không thể chuyển thành JSON.
        Hàm nên bỏ qua item lỗi và xử lý các item còn lại.
        """
        # 1. Input: set() không thể được serialize bởi json.dumps mặc định
        items_with_error = [
            {"id": 1, "valid": True},
            {"id": 2, "invalid_data": {1, 2, 3}},  # Đây là item sẽ gây lỗi
            {"id": 3, "valid": True},
        ]

        # 2. Action
        gzipped_stream, count = process_items_to_gzipped_ndjson(items_with_error)

        # 3. Assertions
        self.assertEqual(count, 2, "Chỉ có 2 item hợp lệ được xử lý")

        # Kiểm tra nội dung
        decompressed_data = gzip.decompress(gzipped_stream.read()).decode("utf-8")
        result_items = [
            json.loads(line) for line in decompressed_data.strip().split("\n")
        ]

        # Đảm bảo item lỗi không có trong kết quả
        ids_in_result = {item["id"] for item in result_items}
        self.assertIn(1, ids_in_result)
        self.assertIn(3, ids_in_result)
        self.assertNotIn(
            2, ids_in_result, "Item không hợp lệ không nên có trong output"
        )


# Dòng này cho phép chạy file test trực tiếp từ command line
if __name__ == "__main__":
    unittest.main()
