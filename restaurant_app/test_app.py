
import time
import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

class TestRestaurantApp(unittest.TestCase):

    def setUp(self):
        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
        self.driver.get("https://final-tester.onrender.com/")

    def tearDown(self):
        self.driver.quit()

    def test_admin_flow(self):
        # Admin Login
        self.driver.find_element(By.LINK_TEXT, "Login").click()
        time.sleep(1)
        select = Select(self.driver.find_element(By.NAME, 'who'))
        select.select_by_value('admin')
        time.sleep(1)
        self.driver.find_element(By.NAME, "username").send_keys("admin1")
        time.sleep(1)
        self.driver.find_element(By.NAME, "password").send_keys("admin")
        time.sleep(1)
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()
        time.sleep(2)

        # Admin functionality
        self.driver.get("https://final-tester.onrender.com/admin/users")
        time.sleep(2)
        self.driver.get("https://final-tester.onrender.com/admin/restaurants")
        time.sleep(2)
        self.driver.get("https://final-tester.onrender.com/admin/tables")
        time.sleep(2)
        self.driver.get("https://final-tester.onrender.com/admin/reservations")
        time.sleep(2)

    def test_customer_flow(self):
        # Customer Registration
        self.driver.get("https://final-tester.onrender.com/register")
        time.sleep(1)
        self.driver.find_element(By.NAME, "username").send_keys("newuser")
        time.sleep(1)
        self.driver.find_element(By.NAME, "password").send_keys("password")
        time.sleep(1)
        self.driver.find_element(By.NAME, "email").send_keys("newuser@example.com")
        time.sleep(1)
        self.driver.find_element(By.NAME, "full_name").send_keys("New User")
        time.sleep(1)
        self.driver.find_element(By.NAME, "phone").send_keys("1234567890")
        time.sleep(1)
        self.driver.find_element(By.XPATH, "//button[text()='Register']").click()
        time.sleep(2)

        # Customer Login
        self.driver.find_element(By.LINK_TEXT, "Login").click()
        time.sleep(1)
        self.driver.find_element(By.NAME, "username").send_keys("newuser")
        time.sleep(1)
        self.driver.find_element(By.NAME, "password").send_keys("password")
        time.sleep(1)
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()
        time.sleep(2)

if __name__ == "__main__":
    unittest.main()
