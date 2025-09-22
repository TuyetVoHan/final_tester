from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import random

# --- Khởi tạo WebDriver ---
driver = webdriver.Chrome()  # Nếu bạn dùng Firefox thì đổi thành webdriver.Firefox()
driver.maximize_window()

# --- URL website ---
url = "https://final-tester.onrender.com"

# --- Sinh email ngẫu nhiên để tránh trùng ---
random_number = random.randint(1000, 9999)
random_phone = random.randint(1000000000, 9999999999)
test_email = f"testuser{random_number}@gmail.com"
test_password = "Test1234"

# --- Truy cập trang ---
driver.get(url)
time.sleep(3)

# ==============================
# 1. TEST ĐĂNG KÝ TÀI KHOẢN
# ==============================
try:
    # Tìm và bấm nút/đường link đăng ký
    signup_link = driver.find_element(By.LINK_TEXT, "Register")  # thay "Register" theo text nút trên web bạn
    signup_link.click()
    time.sleep(2)

    username_input = driver.find_element(By.NAME, "username")  # đổi NAME nếu khác
    username_input.send_keys(random_number)


    # Nhập password
    password_input = driver.find_element(By.NAME, "password")  # đổi NAME nếu khác
    password_input.send_keys(test_password)

    # Nhập confirm password (nếu có)

    confirm_password_input = driver.find_element(By.NAME, "confirm_password")
    confirm_password_input.send_keys(test_password)

    fullname_input = driver.find_element(By.NAME, "full_name")  # đổi NAME nếu khác
    fullname_input.send_keys('hung')

    email_input = driver.find_element(By.NAME, "email")  # đổi NAME nếu khác
    email_input.send_keys(test_email)

    phone_input = driver.find_element(By.NAME, "phone")  # đổi NAME nếu khác
    phone_input.send_keys(random_phone)


    # Bấm nút Submit
    submit_btn = driver.find_element(By.CSS_SELECTOR, "button.button.is-primary")
    submit_btn.click()
    time.sleep(4)


    print(f"[OK] Đăng ký thành công với email: {test_email}")
except Exception as e:
    print("[FAIL] Lỗi khi đăng ký:", e)

# ==============================
# 2. TEST ĐĂNG NHẬP TÀI KHOẢN
# ==============================
try:
    # Trở về trang login
    login_link = driver.find_element(By.LINK_TEXT, "Login")  # thay text nếu khác
    login_link.click()
    time.sleep(2)

    username_input = driver.find_element(By.NAME, "username")  # đổi NAME nếu khác
    username_input.send_keys(random_number)

    # Nhập password
    login_password_input = driver.find_element(By.NAME, "password")
    login_password_input.send_keys('hung1234')

    # Bấm nút Submit
    login_submit_btn = driver.find_element(By.CSS_SELECTOR, "button.button.is-primary")
    login_submit_btn.click()
    time.sleep(4)

    print(f"[OK] Đăng nhập thành công với email: {test_email}")
except Exception as e:
    print("[FAIL] Lỗi khi đăng nhập:", e)

# --- Đợi quan sát rồi đóng ---
time.sleep(5)
driver.quit()
