import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime, timedelta

# URL của ứng dụng đã được triển khai
BASE_URL = "https://cuongadmin.pythonanywhere.com/"

class AutomationTest(unittest.TestCase):

    def setUp(self):
        """Khởi tạo trình duyệt Chrome trước mỗi bài test."""
        self.driver = webdriver.Chrome()
        self.driver.implicitly_wait(5)
        self.wait = WebDriverWait(self.driver, 10)

    def tearDown(self):
        """Đóng trình duyệt sau khi mỗi bài test hoàn thành."""
        self.driver.quit()

    # Chức năng Đăng nhập
    def test_AT_LGN_01_valid_login(self):
        driver = self.driver
        driver.get(BASE_URL + "login")
        driver.find_element(By.NAME, "username").send_keys("cuong")
        driver.find_element(By.NAME, "password").send_keys("admin")
        driver.find_element(By.CSS_SELECTOR, "button.is-primary").click()
        self.wait.until(EC.url_to_be(BASE_URL))
        self.assertIn("John Doe", driver.page_source)

    def test_AT_LGN_02_invalid_password(self):
        driver = self.driver
        driver.get(BASE_URL + "login")
        driver.find_element(By.NAME, "username").send_keys("cuong")
        driver.find_element(By.NAME, "password").send_keys("wrongpassword")
        driver.find_element(By.CSS_SELECTOR, "button.is-primary").click()
        error_msg = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".notification.is-danger"))).text
        self.assertIn("Invalid username or password.", error_msg)

    def test_AT_LGN_03_nonexistent_user(self):
        """TC AT_LGN_03: Kiểm tra đăng nhập với username không tồn tại."""
        driver = self.driver
        driver.get(BASE_URL + "login")
        driver.find_element(By.NAME, "username").send_keys("nonexistentuser")
        driver.find_element(By.NAME, "password").send_keys("anypassword")
        driver.find_element(By.CSS_SELECTOR, "button.is-primary").click()
        error_msg = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".notification.is-danger"))).text
        self.assertIn("Invalid username or password.", error_msg)
    # search
    def test_AT_SRC_01_search_by_location_found(self):
        driver = self.driver
        driver.get(BASE_URL + "restaurants")
        driver.find_element(By.NAME, "location").send_keys("Hanoi")
        driver.find_element(By.CSS_SELECTOR, "button.is-info").click()
        restaurants = self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".box ")))

        self.assertEqual(len(restaurants), 1)

        self.assertIn("The Golden Spoon", restaurants[0].text)

    def test_AT_SRC_03_search_not_found(self):
        """TC AT_SRC_03: Tìm kiếm với địa điểm không có kết quả."""
        driver = self.driver
        driver.get(BASE_URL + "restaurants")
        driver.find_element(By.NAME, "location").send_keys("Atlantis")
        driver.find_element(By.CSS_SELECTOR, "button.is-info").click()
        no_results_msg = self.wait.until(
            EC.presence_of_element_located((By.XPATH, "//p[contains(text(), 'No restaurants found.')]"))).text
        self.assertEqual("No restaurants found.", no_results_msg)

    def test_AT_SRC_04_search_empty_string(self):
        driver = self.driver
        driver.get(BASE_URL + "restaurants")

        # Không nhập gì vào location, bấm search
        driver.find_element(By.NAME, "location").send_keys("")
        driver.find_element(By.CSS_SELECTOR, "button.is-info").click()
        time.sleep(2)

        # Lấy danh sách tất cả restaurants
        restaurants = self.wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".box h3.is-4"))
        )

        # Assert: Có nhiều hơn 0 nhà hàng (không bị lọc)
        self.assertGreater(len(restaurants), 0)
    def test_AT_SRC_05_search_sql_injection(self):
        driver = self.driver
        driver.get(BASE_URL + "restaurants")

        # Nhập chuỗi SQL Injection
        driver.find_element(By.NAME, "location").send_keys("' OR 1=1;--")
        driver.find_element(By.CSS_SELECTOR, "button.is-info").click()
        time.sleep(2)

        # Kiểm tra kết quả (không bị lỗi, không hiển thị tất cả nhà hàng)
        restaurants = driver.find_elements(By.CSS_SELECTOR, ".box h3.is-4")

        # Có thể là 0 hoặc rất ít, nhưng không được crash
        self.assertTrue(len(restaurants) == 0 )

    def test_AT_SRC_06_search_multiple_filters(self):
        driver = self.driver
        driver.get(BASE_URL + "restaurants")

        # Nhập location = New York
        driver.find_element(By.NAME, "location").send_keys("New York")

        driver.find_element(By.NAME, "cuisine").send_keys("Italian")

        # Bấm search
        driver.find_element(By.CSS_SELECTOR, "button.is-info").click()
        time.sleep(2)

        # Lấy danh sách kết quả
        restaurants = self.wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".box h3.is-4"))
        )

        # Assert: Có ít nhất 1 restaurant và text phải chứa Italian
        self.assertGreater(len(restaurants), 0)
        for r in restaurants:
            self.assertIn("Italian", r.text)
    # Chức năng Đặt bàn

    def test_AT_REV_01_make_reservation_success(self):
        driver = self.driver
        driver.get(BASE_URL + "login")
        driver.find_element(By.NAME, "username").send_keys("cuong")
        driver.find_element(By.NAME, "password").send_keys("admin")
        driver.find_element(By.CSS_SELECTOR, "button.is-primary").click()

        driver.get(BASE_URL + "restaurant/1")  # Pizza Palace
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        driver.find_element(By.NAME, "date").send_keys(tomorrow)
        driver.find_element(By.NAME, "time").send_keys("20:30")
        driver.find_element(By.NAME, "guests").send_keys("3")
        driver.find_element(By.CSS_SELECTOR, "button.is-primary").click()
        self.wait.until(EC.url_to_be(BASE_URL + "bookings"))
        self.assertIn("Reservation created", driver.page_source)

    def test_AT_REV_02_fail_on_past_date(self):
        """TC AT_REV_02: Cố gắng đặt bàn vào một ngày trong quá khứ."""
        driver = self.driver
        driver.get(BASE_URL + "login")
        driver.find_element(By.NAME, "username").send_keys("cuong")
        driver.find_element(By.NAME, "password").send_keys("admin")
        driver.find_element(By.CSS_SELECTOR, "button.is-primary").click()

        driver.get(BASE_URL + "restaurant/1")
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        date_input = driver.find_element(By.NAME, "date")
        # Selenium không cho phép set giá trị nhỏ hơn min, ta sẽ dùng javascript
        driver.execute_script(f"arguments[0].value = '{yesterday}';", date_input)
        driver.find_element(By.NAME, "time").send_keys("19:00")
        driver.find_element(By.NAME, "guests").send_keys("2")
        driver.find_element(By.CSS_SELECTOR, "button.is-primary").click()

        error_msg = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".notification.is-danger"))).text
        self.assertIn("You cannot make a reservation for a past date.", error_msg)

    # Chức năng Hủy đặt bàn

    def test_AT_CAN_01_cancel_reservation(self):
        driver = self.driver
        driver.get(BASE_URL + "login")
        driver.find_element(By.NAME, "username").send_keys("cuong")
        driver.find_element(By.NAME, "password").send_keys("admin")
        driver.find_element(By.CSS_SELECTOR, "button.is-primary").click()

        driver.get(BASE_URL + "restaurant/3")
        two_days_later = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
        driver.find_element(By.NAME, "date").send_keys(two_days_later)
        driver.find_element(By.NAME, "time").send_keys("12:00")
        driver.find_element(By.NAME, "guests").send_keys("2")
        driver.find_element(By.CSS_SELECTOR, "button.is-primary").click()

        self.wait.until(EC.url_to_be(BASE_URL + "bookings"))
        driver.find_element(By.CSS_SELECTOR, ".box .buttons a.is-info").click()

        self.wait.until(EC.presence_of_element_located((By.NAME, "action")))
        driver.find_element(By.NAME, "action").click()
        self.wait.until(EC.url_to_be(BASE_URL + "bookings"))
        self.assertIn("Reservation cancelled.", driver.page_source)

if __name__ == '__main__':
    unittest.main(verbosity=2)