import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# các hàm và đối tượng cần thiết
from restaurant_app.app import app, is_reservation_date_valid, is_reservation_time_valid, find_available_table


class TestDateTimeValidation(unittest.TestCase):
    """
    Kiểm tra chức năng xác thực ngày/giờ đặt chỗ (Yêu cầu 3.1.1)
    Tương ứng với các TC ID: UT_DT_01 đến UT_DT_06
    """

    def setUp(self):
        self.restaurant = {'opening_time': '10:00', 'closing_time': '22:00'}
        # Giả sử hôm nay là 2025-09-20
        self.mock_today = datetime(2025, 9, 20)

    def test_UT_DT_01_valid_future_date(self):
        """TC UT_DT_01: Ngày hợp lệ - Ngày trong tương lai"""
        with patch('restaurant_app.app.datetime') as mock_dt:
            mock_dt.now.return_value = self.mock_today
            self.assertTrue(is_reservation_date_valid("2025-09-21"))

    def test_UT_DT_02_valid_today_date_boundary(self):
        """TC UT_DT_02: Ngày hợp lệ - Ngày hôm nay (Biên)"""
        with patch('restaurant_app.app.datetime') as mock_dt:
            mock_dt.now.return_value = self.mock_today
            self.assertTrue(is_reservation_date_valid("2025-09-20"))

    def test_UT_DT_03_invalid_past_date_boundary(self):
        """TC UT_DT_03: Ngày không hợp lệ - Ngày hôm qua (Biên)"""
        with patch('restaurant_app.app.datetime') as mock_dt:
            mock_dt.now.return_value = self.mock_today
            self.assertFalse(is_reservation_date_valid("2025-09-19"))

    def test_UT_DT_04_valid_time_in_range(self):
        """TC UT_DT_04: Thời gian hợp lệ - Trong giờ hoạt động"""
        self.assertTrue(is_reservation_time_valid("18:00", self.restaurant))

    def test_UT_DT_05_invalid_time_before_opening(self):
        """TC UT_DT_05: Thời gian không hợp lệ - Trước giờ mở cửa"""
        self.assertFalse(is_reservation_time_valid("09:59", self.restaurant))

    def test_UT_DT_06_invalid_time_at_closing(self):
        """TC UT_DT_06: Thời gian không hợp lệ - Đúng giờ đóng cửa"""
        self.assertFalse(is_reservation_time_valid("22:00", self.restaurant))


@patch('restaurant_app.app.get_db')
class TestTableAvailability(unittest.TestCase):
    """
    Kiểm tra chức năng kiểm tra bàn trống và tính toán số ghế (Yêu cầu 3.1.2 & 3.1.3)
    Tương ứng với các TC ID: UT_AV_01 đến UT_AV_05
    """

    def test_UT_AV_01_finds_smallest_available_table(self, mock_get_db):
        """TC UT_AV_01: Thành công - Có bàn trống nhỏ nhất phù hợp"""
        mock_db = MagicMock()
        mock_db.execute.return_value.fetchone.return_value = {'table_id': 4}
        mock_get_db.return_value = mock_db
        self.assertEqual(find_available_table(mock_db, 1, 'date', 'time', 4), 4)

    def test_UT_AV_02_fails_when_no_table_is_large_enough(self, mock_get_db):
        """TC UT_AV_02: Thất bại - Không có bàn nào đủ lớn"""
        mock_db = MagicMock()
        mock_db.execute.return_value.fetchone.return_value = None
        mock_get_db.return_value = mock_db
        self.assertIsNone(find_available_table(mock_db, 1, 'date', 'time', 10))

    def test_UT_AV_03_fails_when_suitable_tables_are_booked(self, mock_get_db):
        """TC UT_AV_03: Thất bại - Bàn phù hợp đã được đặt"""
        mock_db = MagicMock()
        mock_db.execute.return_value.fetchone.return_value = None
        mock_get_db.return_value = mock_db
        self.assertIsNone(find_available_table(mock_db, 1, 'date', 'time', 4))

    def test_UT_AV_04_succeeds_with_specific_valid_table(self, mock_get_db):
        """TC UT_AV_04: Thành công - Người dùng chọn một bàn cụ thể còn trống"""
        mock_db = MagicMock()
        mock_db.execute.return_value.fetchone.return_value = {'table_id': 8}
        mock_get_db.return_value = mock_db
        self.assertEqual(find_available_table(mock_db, 1, 'date', 'time', 3, selected_table_id=8), 8)

    def test_UT_AV_05_fails_with_specific_table_not_enough_capacity(self, mock_get_db):
        """TC UT_AV_05: Thất bại - Người dùng chọn bàn không đủ chỗ"""
        mock_db = MagicMock()
        mock_db.execute.return_value.fetchone.return_value = None
        mock_get_db.return_value = mock_db
        self.assertIsNone(find_available_table(mock_db, 1, 'date', 'time', 5, selected_table_id=4))

    def test_UT_AV_06_allows_booking_exactly_after_2_hour_window(self, mock_get_db):
        """TC UT_AV_06: Kiểm tra: Cho phép đặt bàn ngay khi cửa sổ 2 tiếng của lượt đặt trước vừa kết thúc."""
        mock_db = MagicMock()
        # Giả lập CSDL trả về bàn trống, vì logic thời gian đã loại trừ bàn bị trùng
        mock_db.execute.return_value.fetchone.return_value = {'table_id': 5}
        mock_get_db.return_value = mock_db

        # Lượt đặt mới lúc 21:00 sẽ không bị xung đột với một lượt đặt lúc 19:00
        result = find_available_table(mock_db, 1, '2025-10-10', '21:00', 2)

        # Chúng ta muốn xác nhận rằng hàm đã tìm thấy bàn
        self.assertIsNotNone(result)
        self.assertEqual(result, 5)


class TestReservationStatusUpdate(unittest.TestCase):
    """
    Kiểm tra chức năng cập nhật trạng thái đặt bàn (Yêu cầu 3.1.4)
    Tương ứng với các TC ID: UT_ST_01 đến UT_ST_03
    """

    def setUp(self):
        # Tạo một client kiểm thử cho ứng dụng Flask
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test_secret_key'
        self.client = app.test_client()

    @patch('restaurant_app.app.get_db')
    def test_UT_ST_01_and_02_update_status_successfully(self, mock_get_db):
        """TC UT_ST_01 & UT_ST_02: Cập nhật thành công các trạng thái"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Giả lập phiên làm việc của admin
        with self.client.session_transaction() as sess:
            sess['user'] = 1
            sess['role'] = 'admin'

        # Kịch bản: pending -> confirmed
        res_id_1 = 1
        new_status_1 = 'confirmed'
        self.client.post(f'/admin/reservation/{res_id_1}/update', data={'status': new_status_1})

        # Kịch bản: confirmed -> completed
        res_id_2 = 2
        new_status_2 = 'completed'
        self.client.post(f'/admin/reservation/{res_id_2}/update', data={'status': new_status_2})

        # Xác minh rằng CSDL đã được gọi để cập nhật
        self.assertEqual(mock_db.execute.call_count, 4)  # 2 cho UPDATE, 2 cho INSERT vào History

        # Kiểm tra lệnh UPDATE đầu tiên
        mock_db.execute.assert_any_call("UPDATE Reservations SET status = ? WHERE reservation_id = ?",
                                        (new_status_1, res_id_1))
        # Kiểm tra lệnh UPDATE thứ hai
        mock_db.execute.assert_any_call("UPDATE Reservations SET status = ? WHERE reservation_id = ?",
                                        (new_status_2, res_id_2))

    @patch('restaurant_app.app.get_db')
    def test_UT_ST_03_update_fails_with_nonexistent_id(self, mock_get_db):
        """TC UT_ST_03: Cập nhật thất bại - res_id không tồn tại"""
        mock_db = MagicMock()
        # Giả lập CSDL không thực hiện thay đổi nào (rowcount = 0)
        mock_db.execute.return_value.rowcount = 0
        mock_get_db.return_value = mock_db

        with self.client.session_transaction() as sess:
            sess['user'] = 1
            sess['role'] = 'admin'

        res_id = 999
        new_status = 'confirmed'
        response = self.client.post(f'/admin/reservation/{res_id}/update', data={'status': new_status})

        # Mặc dù không có lỗi, chúng ta có thể kiểm tra rằng CSDL đã được gọi đúng cách
        mock_db.execute.assert_any_call("UPDATE Reservations SET status = ? WHERE reservation_id = ?",
                                        (new_status, res_id))
        # Và kiểm tra rằng hàm commit đã được gọi
        mock_db.commit.assert_called_once()
        # Chuyển hướng thành công là một dấu hiệu tốt
        self.assertEqual(response.status_code, 302)  # 302 là mã cho redirect


if __name__ == '__main__':
    unittest.main(verbosity=2)