import unittest
import os
import sys
from datetime import datetime, timedelta

# Thêm thư mục gốc của dự án vào Python Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from restaurant_app.app import app
from restaurant_app.init_database import init_db, DB_PATH


# --- Lớp kiểm thử cho Luồng chức năng Khách hàng (Bảng 7) ---
class CustomerFlowIntegrationTest(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test_secret_key'
        self.client = app.test_client()
        if os.path.exists(DB_PATH): os.remove(DB_PATH)
        init_db()

    def tearDown(self):
        if os.path.exists(DB_PATH): os.remove(DB_PATH)

    def test_IT_FLOW_01_full_customer_journey_success(self):
        """TC IT_FLOW_01: Luồng thành công A-Z từ đăng ký đến xem đặt bàn."""
        # 1. Đăng ký
        self.client.post('/register', data={'username': 'end2enduser', 'password': 'complexpass123',
                                            'confirm_password': 'complexpass123', 'email': 'e2e@test.com'})
        # 2. Đăng nhập
        self.client.post('/login', data={'who': 'customer', 'username': 'end2enduser', 'password': 'complexpass123'})
        # 3. Đặt bàn
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        reserve_response = self.client.post('/restaurant/1', data={'date': tomorrow, 'time': '19:00', 'guests': '2'},
                                            follow_redirects=True)
        # 4. Kiểm tra kết quả
        self.assertIn(b'Reservation created', reserve_response.data)
        self.assertIn(b'Pizza Palace', reserve_response.data)
        self.assertIn(b'pending', reserve_response.data)

    def test_IT_FLOW_02_reservation_fails_if_not_logged_in(self):
        """TC IT_FLOW_02: Luồng thất bại - Đặt bàn khi chưa đăng nhập."""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        response = self.client.post('/restaurant/1', data={'date': tomorrow, 'time': '19:00', 'guests': '2'},
                                    follow_redirects=True)
        self.assertIn(b'Please login as a customer', response.data)
        # SỬA LỖI: Tìm chuỗi HTML chính xác hơn
        self.assertIn(b'<h2 class="title">Login</h2>', response.data)

    def test_IT_FLOW_03_edit_reservation_fails_no_table(self):
        """TC IT_FLOW_03: Luồng thất bại - Sửa đặt bàn nhưng không còn bàn trống phù hợp."""
        self.client.post('/login', data={'who': 'customer', 'username': 'cuong', 'password': 'admin'})
        # SỬA LỖI: Logic chiếm bàn đã được sửa lại cho đúng
        # Đặt bàn T3 (6 chỗ)
        self.client.post('/restaurant/1', data={'date': '2025-11-10', 'time': '20:00', 'guests': '6'})  # res_id=1
        # Đặt bàn T2 (4 chỗ)
        self.client.post('/restaurant/1', data={'date': '2025-11-10', 'time': '20:00', 'guests': '4'})  # res_id=2
        # Đặt bàn T1 (2 chỗ)
        self.client.post('/restaurant/1', data={'date': '2025-11-10', 'time': '20:00', 'guests': '2'})  # res_id=3

        # Bây giờ, cố gắng sửa lượt đặt res_id=3 từ 2 khách lên 3 khách. Sẽ không còn bàn nào trống để chứa.
        response = self.client.post('/reservation/3/edit', data={'date': '2025-11-10', 'time': '20:00', 'guests': '3'},
                                    follow_redirects=True)
        self.assertIn(b'No available table for updated time/party size.', response.data)


# --- Lớp kiểm thử cho Tích hợp Bàn trống (Bảng 8) ---
class AvailabilityIntegrationTest(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        if os.path.exists(DB_PATH): os.remove(DB_PATH)
        init_db()

    def tearDown(self):
        if os.path.exists(DB_PATH): os.remove(DB_PATH)

    def test_IT_AVAIL_01_booking_conflict(self):
        """TC IT_AVAIL_01: User 1 đặt thành công, User 2 đặt trùng giờ thất bại."""
        self.client.post('/login', data={'who': 'customer', 'username': 'cuong', 'password': 'admin'})
        # SỬA LỖI: User 1 đặt hết tất cả các bàn tại nhà hàng Sushi World (id=2)
        self.client.post('/restaurant/2', data={'date': '2025-11-11', 'time': '19:30', 'guests': '2'}) # Đặt bàn T1
        self.client.post('/restaurant/2', data={'date': '2025-11-11', 'time': '19:30', 'guests': '4'}) # Đặt bàn T2
        self.client.post('/restaurant/2', data={'date': '2025-11-11', 'time': '19:30', 'guests': '6'}) # Đặt bàn T3
        self.client.get('/logout')

        # User 2 đăng ký, đăng nhập và cố gắng đặt bàn
        self.client.post('/register', data={'username': 'user2', 'password': 'password123', 'confirm_password': 'password123', 'email': 'user2@test.com'})
        self.client.post('/login', data={'who': 'customer', 'username': 'user2', 'password': 'password123'})
        response = self.client.post('/restaurant/2', data={'date': '2025-11-11', 'time': '19:30', 'guests': '2'}, follow_redirects=True)
        self.assertIn(b'No available table', response.data)

    def test_IT_AVAIL_02_cancel_and_rebook(self):
        self.client.post('/login', data={'who': 'customer', 'username': 'cuong', 'password': 'admin'})
        self.client.post('/restaurant/2', data={'date': '2025-11-12', 'time': '20:00', 'guests': '2'}) # res_id=1
        self.client.post('/reservation/1/edit', data={'action': 'cancel'})
        self.client.get('/logout')

        self.client.post('/register', data={'username': 'user2', 'password': 'password123', 'confirm_password': 'password123', 'email': 'user2@test.com'})
        self.client.post('/login', data={'who': 'customer', 'username': 'user2', 'password': 'password123'})
        response = self.client.post('/restaurant/2', data={'date': '2025-11-12', 'time': '20:00', 'guests': '2'}, follow_redirects=True)
        self.assertIn(b'Reservation created', response.data)


# --- Lớp kiểm thử cho Tích hợp Admin-Customer (Bảng 9) ---
class AdminCustomerSyncIntegrationTest(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        if os.path.exists(DB_PATH): os.remove(DB_PATH)
        init_db()

    def tearDown(self):
        if os.path.exists(DB_PATH): os.remove(DB_PATH)

    def test_IT_SYNC_01_admin_confirms_reservation(self):
        """TC IT_SYNC_01: Admin xác nhận, khách hàng thấy trạng thái 'confirmed'."""
        # 1. Customer 'cuong' đặt bàn -> res_id=1, status=pending
        self.client.post('/login', data={'who': 'customer', 'username': 'cuong', 'password': 'admin'})
        self.client.post('/restaurant/1', data={'date': '2025-10-10', 'time': '19:00', 'guests': '2'})

        # 2. Admin đăng nhập và cập nhật
        self.client.post('/login', data={'who': 'admin', 'username': 'admin1', 'password': 'admin'})
        self.client.post('/admin/reservation/1/update', data={'status': 'confirmed'})

        # 3. Customer kiểm tra lại
        self.client.post('/login', data={'who': 'customer', 'username': 'cuong', 'password': 'admin'})
        bookings_page = self.client.get('/bookings')
        self.assertIn(b'confirmed', bookings_page.data)

    def test_IT_SYNC_02_admin_rejects_reservation(self):
        """TC IT_SYNC_02: Admin từ chối, khách hàng thấy trạng thái 'rejected'."""
        self.client.post('/login', data={'who': 'customer', 'username': 'cuong', 'password': 'admin'})
        self.client.post('/restaurant/1', data={'date': '2025-10-11', 'time': '20:00', 'guests': '3'})  # res_id=1

        self.client.post('/login', data={'who': 'admin', 'username': 'admin1', 'password': 'admin'})
        self.client.post('/admin/reservation/1/update', data={'status': 'rejected'})

        self.client.post('/login', data={'who': 'customer', 'username': 'cuong', 'password': 'admin'})
        bookings_page = self.client.get('/bookings')
        self.assertIn(b'rejected', bookings_page.data)

    def test_IT_SYNC_03_admin_completes_reservation(self):
        """TC IT_SYNC_03: Admin hoàn thành, khách hàng thấy trạng thái 'completed'."""
        self.client.post('/login', data={'who': 'customer', 'username': 'cuong', 'password': 'admin'})
        self.client.post('/restaurant/1', data={'date': '2025-10-12', 'time': '21:00', 'guests': '4'})  # res_id=1

        self.client.post('/login', data={'who': 'admin', 'username': 'admin1', 'password': 'admin'})
        # Trạng thái phải là 'confirmed' trước khi 'completed'
        self.client.post('/admin/reservation/1/update', data={'status': 'confirmed'})
        self.client.post('/admin/reservation/1/update', data={'status': 'completed'})

        self.client.post('/login', data={'who': 'customer', 'username': 'cuong', 'password': 'admin'})
        bookings_page = self.client.get('/bookings')
        self.assertIn(b'completed', bookings_page.data)


if __name__ == '__main__':
    unittest.main(verbosity=2)