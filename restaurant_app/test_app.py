import time
import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

class TestCustomerFlow(unittest.TestCase):

    def setUp(self):
        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
        self.driver.get("https://final-tester.onrender.com/")
        # Pre-register a user for testing
        self.register_user("testuser", "password", "testuser@example.com", "Test User", "1234567890")

    def tearDown(self):
        self.driver.quit()

    def register_user(self, username, password, email, full_name, phone):
        self.driver.get("https://final-tester.onrender.com/register")
        time.sleep(1)
        self.driver.find_element(By.NAME, "username").send_keys(username)
        self.driver.find_element(By.NAME, "password").send_keys(password)
        self.driver.find_element(By.NAME, "confirm_password").send_keys(password)
        self.driver.find_element(By.NAME, "email").send_keys(email)
        self.driver.find_element(By.NAME, "full_name").send_keys(full_name)
        self.driver.find_element(By.NAME, "phone").send_keys(phone)
        self.driver.find_element(By.XPATH, "//button[text()='Register']").click()
        time.sleep(2)
        # Go back to the homepage after registration
        self.driver.get("https://final-tester.onrender.com/")

    def login(self, username, password):
        self.driver.find_element(By.LINK_TEXT, "Login").click()
        time.sleep(1)
        self.driver.find_element(By.NAME, "username").send_keys(username)
        self.driver.find_element(By.NAME, "password").send_keys(password)
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()
        time.sleep(2)

    def test_login(self):
        # Test invalid login
        self.login("wronguser", "wrongpassword")
        self.assertIn("Invalid credentials", self.driver.page_source)

        # Test valid login
        self.login("testuser", "password")
        self.assertIn("Welcome", self.driver.page_source)

    def test_search_restaurant(self):
        self.login("testuser", "password")
        self.driver.get("https://final-tester.onrender.com/restaurants")
        time.sleep(1)
        self.driver.find_element(By.NAME, "query").send_keys("Pizza")
        self.driver.find_element(By.XPATH, "//button[text()='Search']").click()
        time.sleep(2)
        self.assertIn("Pizza Place", self.driver.page_source)

    def test_make_reservation(self):
        self.login("testuser", "password")
        self.driver.get("https://final-tester.onrender.com/restaurant/1") # Assuming restaurant with ID 1 exists
        time.sleep(1)
        self.driver.find_element(By.NAME, "date").send_keys("2025-12-31")
        self.driver.find_element(By.NAME, "time").send_keys("19:00")
        self.driver.find_element(By.NAME, "guests").send_keys("2")
        self.driver.find_element(By.XPATH, "//button[text()='Book Now']").click()
        time.sleep(2)
        self.assertIn("Reservation successful!", self.driver.page_source)
        self.driver.get("https://final-tester.onrender.com/bookings")
        self.assertIn("2025-12-31", self.driver.page_source)


    def test_cancel_reservation(self):
        # First, make a reservation to cancel
        self.test_make_reservation()

        self.driver.get("https://final-tester.onrender.com/bookings")
        time.sleep(1)
        # This assumes the cancel button is a link with the text 'Cancel'
        # and it's the first one on the page.
        # A more robust selector would be needed for a real application
        cancel_button = self.driver.find_element(By.XPATH, "//a[contains(@href, '/cancel_booking/')]")
        cancel_button.click()
        time.sleep(2)
        # After cancellation, the user might be redirected or the page updated.
        # We'll check if the reservation is gone.
        self.assertNotIn("2025-12-31", self.driver.page_source)


if __name__ == "__main__":
    unittest.main()