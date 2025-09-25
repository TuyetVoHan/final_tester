import unittest
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.chrome.options import Options

# URL của ứng dụng đã được triển khai
BASE_URL = "https://cuongadmin.pythonanywhere.com/"

class AutomationTest(unittest.TestCase):

    def setUp(self):
        """Khởi tạo trình duyệt Chrome trước mỗi bài test."""
        chrome_options = Options()
        chrome_options.add_argument("--lang=vi-VN")
        chrome_options.add_experimental_option('prefs', {'intl.accept_languages': 'vi-VN,vi'})

        self.driver = webdriver.Chrome(options=chrome_options)
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

        driver.find_element(By.NAME, "location").send_keys("New York")
        driver.find_element(By.NAME, "cuisine").send_keys("Italian")
        driver.find_element(By.CSS_SELECTOR, "button.is-info").click()
        time.sleep(2)
        restaurants = self.wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".box"))
        )

        self.assertGreater(len(restaurants), 0)
        for r in restaurants:
            self.assertIn("Italian", r.text)

    # Chức năng Đặt bàn
    # def test_AT_REV_01_make_reservation_success(self):
    #     driver = self.driver
    #     driver.get(BASE_URL)
    #
    #     # Sinh dữ liệu ngẫu nhiên
    #     random_number = random.randint(1000, 9999)
    #     random_phone = random.randint(1000000000, 9999999999)
    #     test_email = f"testuser{random_number}@gmail.com"
    #     test_password = f"Test@{random_phone}"   # password mạnh hơn
    #
    #     # --- Đăng ký ---
    #     driver.find_element(By.LINK_TEXT, "Register").click()
    #
    #     driver.find_element(By.NAME, "username").send_keys(f"user{random_number}")
    #     driver.find_element(By.NAME, "password").send_keys(test_password)
    #     driver.find_element(By.NAME, "confirm_password").send_keys(test_password)
    #     driver.find_element(By.NAME, "full_name").send_keys("Hung")
    #     driver.find_element(By.NAME, "email").send_keys(test_email)
    #     driver.find_element(By.NAME, "phone").send_keys(str(random_phone))
    #     driver.find_element(By.CSS_SELECTOR, "button.button.is-primary").click()
    #
    #
    #     # --- Đăng nhập ---
    #     driver.find_element(By.LINK_TEXT, "Login").click()
    #     driver.find_element(By.NAME, "username").send_keys(f"user{random_number}")
    #     driver.find_element(By.NAME, "password").send_keys(test_password)
    #     driver.find_element(By.CSS_SELECTOR, "button.button.is-primary").click()
    #
    #
    #
    #     driver.find_element(By.LINK_TEXT, "Restaurants").click()
    #
    #     driver.find_element(By.CSS_SELECTOR, "a.button.is-small.is-primary").click()
    #
    #     driver.find_element(By.LINK_TEXT, "Restaurants").click()
    #
    #     driver.find_element(By.CSS_SELECTOR, "a.button.is-small.is-primary").click()
    #
    #     tomorrow = (date.today() + timedelta(days=2)).strftime("%y-%m-%d")
    #     print (tomorrow)
    #
    #     date_input = driver.find_element(By.NAME, "date")
    #
    #     driver.execute_script("arguments[0].value = arguments[1];", date_input, tomorrow)
    #
    #
    #     driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", date_input)
    #
    #     time_input = driver.find_element(By.NAME, "time")
    #
    #     # Xóa giá trị cũ nếu có
    #     time_input.clear()
    #
    #     time_input = driver.find_element(By.NAME, "time")
    #
    #     # Đặt trực tiếp giá trị bằng JavaScript (24h format)
    #     driver.execute_script("arguments[0].value = '20:30';", time_input)
    #
    #     # Nếu cần, có thể trigger sự kiện change để form nhận giá trị
    #     driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", time_input)
    #
    #
    #     driver.find_element(By.NAME, "guests").send_keys("3")
    #     driver.find_element(By.CSS_SELECTOR, "button.is-primary").click()
    #
    #     # Kiểm tra thông báo đặt bàn thành công
    #     success_reserve = self.wait.until(
    #         EC.presence_of_element_located((By.CSS_SELECTOR, ".notification.is-success"))
    #     )
    #     self.assertIn("Reservation created and is pending confirmation.", success_reserve.text)

    def test_AT_REV_01_make_reservation_success(self):
        """TC AT_REV_01: Đặt bàn thành công."""
        driver = self.driver
        driver.get(BASE_URL + "login")
        self.wait.until(EC.visibility_of_element_located((By.NAME, "username"))).send_keys("cuong1")
        driver.find_element(By.NAME, "password").send_keys("asdasdasd")
        driver.find_element(By.CSS_SELECTOR, "button.is-primary").click()
        self.wait.until(EC.url_to_be(BASE_URL))

        driver.get(BASE_URL + "restaurant/1")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

        # SỬA LỖI: Sử dụng JavaScript để điền ngày một cách đáng tin cậy
        date_input = self.wait.until(EC.visibility_of_element_located((By.NAME, "date")))
        driver.execute_script(f"arguments[0].value = '{tomorrow}';", date_input)

        self.wait.until(EC.visibility_of_element_located((By.NAME, "time"))).send_keys("0830C")  # Gửi 08:30 PM
        self.wait.until(EC.visibility_of_element_located((By.NAME, "guests"))).send_keys("3")
        time.sleep(3)
        self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.is-primary"))).click()

        self.wait.until(EC.url_to_be(BASE_URL + "bookings"))
        self.assertIn("Reservation created", driver.page_source)

    def test_AT_REV_02_fail_on_past_date(self):
        """TC AT_REV_02: (Tiêu cực) Thất bại khi đặt bàn vào ngày trong quá khứ."""
        driver = self.driver
        driver.get(BASE_URL + "login")
        driver.find_element(By.NAME, "username").send_keys("cuong")
        driver.find_element(By.NAME, "password").send_keys("admin")
        driver.find_element(By.CSS_SELECTOR, "button.is-primary").click()
        self.wait.until(EC.url_to_be(BASE_URL))

        driver.get(BASE_URL + "restaurant/1")
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        date_input = driver.find_element(By.NAME, "date")
        driver.execute_script(f"arguments[0].value = '{yesterday}';", date_input)

        driver.find_element(By.NAME, "time").send_keys("19:00")
        driver.find_element(By.NAME, "guests").send_keys("2")
        driver.find_element(By.CSS_SELECTOR, "button.is-primary").click()

        error_msg = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".notification.is-danger"))).text
        self.assertIn("You cannot make a reservation for a past date.", error_msg)

    def test_AT_REV_03_fail_when_restaurant_closed(self):
        """TC AT_REV_03: (Tiêu cực) Thất bại khi đặt bàn ngoài giờ hoạt động."""
        driver = self.driver
        driver.get(BASE_URL + "login")
        driver.find_element(By.NAME, "username").send_keys("cuong")
        driver.find_element(By.NAME, "password").send_keys("admin")
        driver.find_element(By.CSS_SELECTOR, "button.is-primary").click()
        self.wait.until(EC.url_to_be(BASE_URL))

        driver.get(BASE_URL + "restaurant/1")  # Pizza Palace (mở cửa 11:00 - 22:00)
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        driver.find_element(By.NAME, "date").send_keys(tomorrow)
        driver.find_element(By.NAME, "time").send_keys("23:00")
        driver.find_element(By.NAME, "guests").send_keys("2")
        driver.find_element(By.CSS_SELECTOR, "button.is-primary").click()

        error_msg = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".notification.is-danger"))).text
        self.assertIn("the restaurant is only open from", error_msg)

    def test_AT_REV_04_fail_on_empty_required_fields(self):
        """TC AT_REV_04: Thất bại khi để trống trường bắt buộc."""
        driver = self.driver
        driver.get(BASE_URL + "login")
        driver.find_element(By.NAME, "username").send_keys("cuong")
        driver.find_element(By.NAME, "password").send_keys("admin")
        driver.find_element(By.CSS_SELECTOR, "button.is-primary").click()
        self.wait.until(EC.url_to_be(BASE_URL))

        driver.get(BASE_URL + "restaurant/1")
        driver.find_element(By.CSS_SELECTOR, "button.is-primary").click()
        self.assertTrue(driver.current_url.startswith(BASE_URL + "restaurant/1"))
        # Kiểm tra xem trình duyệt có hiển thị thông báo validation hay không
        date_input = driver.find_element(By.NAME, "date")
        self.assertEqual(date_input.get_attribute("validationMessage"), "Please fill out this field.")

    def test_AT_REV_05_fail_on_zero_guests(self):
        """TC AT_REV_05: Thất bại khi đặt bàn cho 0 khách."""
        driver = self.driver
        driver.get(BASE_URL + "login")
        driver.find_element(By.NAME, "username").send_keys("cuong")
        driver.find_element(By.NAME, "password").send_keys("admin")
        driver.find_element(By.CSS_SELECTOR, "button.is-primary").click()
        self.wait.until(EC.url_to_be(BASE_URL))

        driver.get(BASE_URL + "restaurant/1")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        driver.find_element(By.NAME, "date").send_keys(tomorrow)
        driver.find_element(By.NAME, "time").send_keys("20:00")
        driver.find_element(By.NAME, "guests").send_keys("0")
        driver.find_element(By.CSS_SELECTOR, "button.is-primary").click()
        self.assertTrue(driver.current_url.startswith(BASE_URL + "restaurant/1"))
        guests_input = driver.find_element(By.NAME, "guests")
        self.assertIn("Value must be greater than or equal to 1", guests_input.get_attribute("validationMessage"))

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