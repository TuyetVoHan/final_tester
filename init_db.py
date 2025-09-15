import os
import psycopg2
from werkzeug.security import generate_password_hash

def initialize_database():
    """
    Kết nối tới cơ sở dữ liệu PostgreSQL và tạo tất cả các bảng,
    sau đó chèn dữ liệu mẫu.
    """
    # Lấy chuỗi kết nối từ biến môi trường mà Render cung cấp
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        raise RuntimeError("Lỗi: Biến môi trường DATABASE_URL chưa được thiết lập.")

    print("Đang kết nối tới cơ sở dữ liệu...")
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    print("Kết nối thành công. Bắt đầu tạo bảng...")

    # Chạy các lệnh CREATE TABLE đã được điều chỉnh cho PostgreSQL
    
    # 1. Customers
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Customers (
        customer_id   SERIAL PRIMARY KEY,
        username      TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name     TEXT,
        email         TEXT UNIQUE NOT NULL,
        phone         TEXT,
        created_at    DATE DEFAULT CURRENT_DATE
    );
    """)
    print("-> Đã tạo bảng Customers.")

    # 2. Admins
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Admins (
        admin_id      SERIAL PRIMARY KEY,
        adminname     TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name     TEXT,
        email         TEXT UNIQUE NOT NULL,
        created_at    DATE DEFAULT CURRENT_DATE
    );
    """)
    print("-> Đã tạo bảng Admins.")

    # 3. Restaurants
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Restaurants (
        restaurant_id SERIAL PRIMARY KEY,
        name          TEXT NOT NULL,
        location      TEXT NOT NULL,
        cuisine       TEXT,
        rating        REAL CHECK (rating >= 0 AND rating <= 5),
        description   TEXT,
        created_at    DATE DEFAULT CURRENT_DATE
    );
    """)
    print("-> Đã tạo bảng Restaurants.")

    # 4. Tables
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Tables (
        table_id      SERIAL PRIMARY KEY,
        restaurant_id INTEGER NOT NULL REFERENCES Restaurants(restaurant_id) ON DELETE CASCADE,
        table_number  TEXT,
        capacity      INTEGER NOT NULL
    );
    """)
    print("-> Đã tạo bảng Tables.")

    # 5. Reservations
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Reservations (
        reservation_id  SERIAL PRIMARY KEY,
        customer_id     INTEGER NOT NULL REFERENCES Customers(customer_id) ON DELETE CASCADE,
        restaurant_id   INTEGER NOT NULL REFERENCES Restaurants(restaurant_id) ON DELETE CASCADE,
        table_id        INTEGER REFERENCES Tables(table_id) ON DELETE SET NULL,
        reservation_date DATE NOT NULL,
        reservation_time TEXT NOT NULL,
        guests          INTEGER NOT NULL CHECK (guests > 0),
        status          TEXT CHECK (status IN ('pending', 'confirmed', 'rejected', 'completed', 'cancelled')) DEFAULT 'pending',
        created_at      DATE DEFAULT CURRENT_DATE
    );
    """)
    print("-> Đã tạo bảng Reservations.")

    # 6. ReservationHistory
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ReservationHistory (
        history_id     SERIAL PRIMARY KEY,
        reservation_id INTEGER NOT NULL REFERENCES Reservations(reservation_id) ON DELETE CASCADE,
        action         TEXT NOT NULL,
        action_by_admin INTEGER REFERENCES Admins(admin_id) ON DELETE SET NULL,
        action_by_customer INTEGER REFERENCES Customers(customer_id) ON DELETE SET NULL,
        action_time    DATE DEFAULT CURRENT_DATE,
        note           TEXT
    );
    """)
    print("-> Đã tạo bảng ReservationHistory.")
    
    print("Tạo bảng hoàn tất. Bắt đầu chèn dữ liệu mẫu...")

    # Chèn dữ liệu mẫu (chỉ chèn nếu bảng trống)
    cur.execute("SELECT COUNT(*) FROM Admins;")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO Admins (adminname, password_hash, full_name, email) VALUES (%s, %s, %s, %s);",
                    ("admin01", generate_password_hash("adminpass"), "Alice Admin", "admin01@example.com"))
        print("-> Đã chèn admin mặc định.")

    cur.execute("SELECT COUNT(*) FROM Customers;")
    if cur.fetchone()[0] == 0:
        customers_data = [
            ("john_doe", generate_password_hash("johnpass"), "John Doe", "john@example.com", "1234567890"),
            ("jane_smith", generate_password_hash("janepass"), "Jane Smith", "jane@example.com", "0987654321"),
        ]
        cur.executemany("INSERT INTO Customers (username, password_hash, full_name, email, phone) VALUES (%s, %s, %s, %s, %s);", customers_data)
        print("-> Đã chèn 2 customer mẫu.")

    cur.execute("SELECT COUNT(*) FROM Restaurants;")
    if cur.fetchone()[0] == 0:
        restaurants_data = [
            ("Pizza Palace", "New York, NY", "Italian", 4.5, "Authentic Italian pizza with fresh ingredients."),
            ("Sushi World", "Los Angeles, CA", "Japanese", 4.7, "Fresh sushi and sashimi with modern twists."),
        ]
        cur.executemany("INSERT INTO Restaurants (name, location, cuisine, rating, description) VALUES (%s, %s, %s, %s, %s);", restaurants_data)
        print("-> Đã chèn 2 nhà hàng mẫu.")
    
    cur.execute("SELECT COUNT(*) FROM Tables;")
    if cur.fetchone()[0] == 0:
        tables_data = [
            (1, "T1", 2), (1, "T2", 4), (1, "T3", 6),
            (2, "T1", 2), (2, "T2", 4), (2, "T3", 6),
        ]
        cur.executemany("INSERT INTO Tables (restaurant_id, table_number, capacity) VALUES (%s, %s, %s);", tables_data)
        print("-> Đã chèn bàn cho các nhà hàng.")

    # Lưu lại các thay đổi
    conn.commit()
    print("Đã commit dữ liệu.")
    
    # Đóng kết nối
    cur.close()
    conn.close()
    print("✅ Hoàn tất! Cơ sở dữ liệu đã được khởi tạo thành công.")

if __name__ == "__main__":
    initialize_database()