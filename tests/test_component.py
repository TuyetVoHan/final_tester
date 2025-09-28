import unittest
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from restaurant_app.app import app
from restaurant_app.init_database import init_db, DB_PATH


class UserComponentTest(unittest.TestCase):

    def setUp(self):
        """Thiết lập môi trường test cho mỗi lần chạy."""
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test_secret_key'
        app.config['DATABASE'] = 'test_db.sqlite'  # Sử dụng CSDL riêng
        self.client = app.test_client()

        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        init_db()

    def tearDown(self):
        """Dọn dẹp sau khi test xong."""
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)

    def test_CT_USR_01_register_success(self):
        """TC CT_USR_01: Đăng ký tài khoản thành công."""
        response = self.client.post('/register', data={
            'username': 'testuser1', 'password': 'password123', 'confirm_password': 'password123',
            'full_name': 'Test User', 'email': 'test@example.com', 'phone': '0987654321'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Account created. Please log in.', response.data)

    def test_CT_USR_02_register_fail_username_exists(self):
        """TC CT_USR_02: Đăng ký thất bại do username đã tồn tại."""
        self.client.post('/register',
                         data={'username': 'testuser1', 'password': 'password123', 'confirm_password': 'password123',
                               'email': 'test1@example.com'})
        response = self.client.post('/register', data={'username': 'testuser1', 'password': 'password123',
                                                       'confirm_password': 'password123', 'email': 'test2@example.com'})
        self.assertIn(b'Username or email already exists.', response.data)

    def test_CT_USR_03_register_fail_password_mismatch(self):
        """TC CT_USR_03: Đăng ký thất bại do mật khẩu không khớp."""
        response = self.client.post('/register', data={
            'username': 'testuser2',
            'password': 'password123',
            'confirm_password': 'password456',  # Mật khẩu không khớp
            'full_name': 'Test User 2',
            'email': 'test2@example.com',
            'phone': '0987654321'
        })
        # Kiểm tra xem thông báo lỗi chính xác có được hiển thị không
        self.assertIn(b'Passwords do not match.', response.data)

    def test_CT_USR_04_login_customer_success(self):
        """TC CT_USR_04: Đăng nhập với vai trò Customer thành công."""
        self.client.post('/register',
                         data={'username': 'testuser1', 'password': 'password123', 'confirm_password': 'password123',
                               'email': 'test@example.com'})
        response = self.client.post('/login',
                                    data={'who': 'customer', 'username': 'testuser1', 'password': 'password123'},
                                    follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Logged in.', response.data)
        self.assertIn(b'Logout', response.data)

    def test_CT_USR_05_login_fail_wrong_password(self):
        """TC CT_USR_05: Đăng nhập thất bại do sai mật khẩu."""
        self.client.post('/register',
                         data={'username': 'testuser1', 'password': 'password123', 'confirm_password': 'password123',
                               'email': 'test@example.com'})
        response = self.client.post('/login',
                                    data={'who': 'customer', 'username': 'testuser1', 'password': 'wrongpassword'})
        self.assertIn(b'Invalid username or password.', response.data)

    def test_CT_USR_06_update_profile_success(self):
        """TC CT_USR_06: Cập nhật hồ sơ cá nhân thành công."""
        self.client.post('/register',
                         data={'username': 'testuser1', 'password': 'password123', 'confirm_password': 'password123',
                               'email': 'test@example.com'})
        self.client.post('/login', data={'username': 'testuser1', 'password': 'password123'})
        response = self.client.post('/profile', data={'full_name': 'Updated Name', 'email': 'updated@example.com',
                                                      'phone': '1234567890'}, follow_redirects=True)
        self.assertIn(b'Profile updated.', response.data)
        self.assertIn(b'Updated Name', response.data)

class RestaurantComponentTest(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test_secret_key'
        self.client = app.test_client()

        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        init_db()

        # Đăng nhập với vai trò admin cho tất cả các test
        with self.client.session_transaction() as sess:
            sess['user'] = 1
            sess['role'] = 'admin'

    def tearDown(self):
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)

    def test_CT_RES_01_admin_add_restaurant_success(self):
        """TC CT_RES_01: Admin thêm một nhà hàng mới thành công."""
        response = self.client.post('/admin/restaurant/new', data={
            'name': 'New Test Cafe', 'location': 'Test City', 'cuisine': 'Coffee', 'rating': '4.8'
        }, follow_redirects=True)
        self.assertIn(b'Restaurant added.', response.data)
        self.assertIn(b'New Test Cafe', response.data)

    def test_CT_RES_02_admin_edit_restaurant_success(self):
        """TC CT_RES_02: Admin chỉnh sửa thông tin một nhà hàng hiện có."""
        # Pizza Palace có ID là 1 trong dữ liệu mẫu
        response = self.client.post('/admin/restaurant/1/edit', data={
            'name': 'Pizza Palace', 'location': 'Updated City', 'cuisine': 'Italian', 'rating': '4.5'
        }, follow_redirects=True)
        self.assertIn(b'Restaurant updated.', response.data)
        self.assertIn(b'Updated City', response.data)

    def test_CT_RES_03_admin_delete_restaurant_success(self):
        """TC CT_RES_03: Admin xóa một nhà hàng."""
        response = self.client.post('/admin/restaurant/1/delete', follow_redirects=True)
        self.assertIn(b'Restaurant deleted.', response.data)
        self.assertNotIn(b'Pizza Palace', response.data)

class ReservationComponentTest(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test_secret_key'
        self.client = app.test_client()

        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        init_db()

        # Đăng nhập với vai trò customer cho tất cả các test
        # User 'cuong' đã được tạo sẵn trong init_db.py
        self.client.post('/login', data={'who': 'customer', 'username': 'cuong', 'password': 'admin'})

    def tearDown(self):
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)

    def test_CT_REV_01_create_reservation_success(self):
        """TC CT_REV_01: Khách hàng tạo một lượt đặt bàn mới thành công."""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        response = self.client.post('/restaurant/1', data={
            'date': tomorrow, 'time': '19:00', 'guests': '2'
        }, follow_redirects=True)
        self.assertIn(b'Reservation created and is pending confirmation.', response.data)
        self.assertIn(b'Pizza Palace', response.data)  # Tên nhà hàng phải có trong trang bookings

    def test_CT_REV_02_create_reservation_fail_no_table(self):
        """TC CT_REV_02: Khách hàng tạo đặt bàn thất bại do hết bàn."""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        # Đặt hết các bàn có sẵn (giả sử đặt cho 100 khách để chắc chắn hết bàn)
        self.client.post('/restaurant/1', data={'date': tomorrow, 'time': '19:00', 'guests': '100'})

        # Cố gắng đặt lại vào cùng thời điểm
        response = self.client.post('/restaurant/1', data={
            'date': tomorrow, 'time': '19:00', 'guests': '2'
        }, follow_redirects=True)
        self.assertIn(b'No available table for that time and party size.', response.data)

    def test_CT_REV_03_edit_reservation_success(self):
        """TC CT_REV_03: Khách hàng chỉnh sửa một lượt đặt bàn thành công."""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        # Bước 1: Tạo một lượt đặt bàn ban đầu với 2 khách (sẽ có reservation_id = 1)
        self.client.post('/restaurant/1', data={'date': tomorrow, 'time': '19:00', 'guests': '2'})

        # Bước 2: Gửi yêu cầu chỉnh sửa để tăng số khách lên 3
        response = self.client.post('/reservation/1/edit', data={
            'date': tomorrow,
            'time': '19:00',
            'guests': '3'  # Thay đổi số khách
        }, follow_redirects=True)

        # Bước 3: Kiểm tra kết quả
        self.assertIn(b'Reservation updated.', response.data)
        # Kiểm tra xem thông tin mới (3 guests) có được hiển thị trên trang không
        self.assertIn(b'3\n    guests', response.data)

    def test_CT_REV_04_cancel_reservation_success(self):
        """TC CT_REV_04: Khách hàng hủy một lượt đặt bàn."""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        # Tạo một lượt đặt bàn trước (sẽ có reservation_id = 1)
        self.client.post('/restaurant/1', data={'date': tomorrow, 'time': '19:00', 'guests': '2'})

        # Hủy lượt đặt bàn đó
        response = self.client.post('/reservation/1/edit', data={'action': 'cancel'}, follow_redirects=True)
        self.assertIn(b'Reservation cancelled.', response.data)
        self.assertIn(b'guests | <em>cancelled</em>', response.data)


if __name__ == '__main__':
    unittest.main(verbosity=2)