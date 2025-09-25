import sqlite3
import csv

# Đường dẫn tới các tệp
DB_PATH = "restaurant_reservation.db"
CSV_PATH = "users_150.csv" # Tệp CSV sẽ được tạo ra ở cùng thư mục

def export_users_to_csv():
    """
    Truy vấn CSDL và xuất username của 400 người dùng mẫu ra tệp CSV.
    """
    print("Connecting to the database...")
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()

    try:
        # Lấy username của các tài khoản từ user1 đến user400
        cur.execute("SELECT username FROM Customers WHERE username LIKE 'user%' LIMIT 150;")
        users = cur.fetchall()
        
        if not users:
            print("No sample users (user1, user2, ...) found in the database.")
            return

        print(f"Found {len(users)} users. Exporting to {CSV_PATH}...")

        with open(CSV_PATH, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Ghi dòng tiêu đề
            writer.writerow(['username', 'password'])
            
            # Ghi dữ liệu cho mỗi người dùng
            for user in users:
                # Mật khẩu chung mà chúng ta đã đặt khi tạo user
                writer.writerow([user[0], 'password123'])
        
        print("Successfully exported users to users.csv")

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()

if __name__ == '__main__':
    export_users_to_csv()