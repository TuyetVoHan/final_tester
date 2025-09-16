import sqlite3
from werkzeug.security import generate_password_hash

# Đường dẫn tới file CSDL, đảm bảo nó giống với trong app.py
DB_PATH = "restaurant_reservation.db"

# -----------------------
# DB initialization
# -----------------------
def init_db():
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")

    # Customers
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Customers (
        customer_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        username      TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name     TEXT,
        email         TEXT UNIQUE NOT NULL,
        phone         TEXT,
        created_at    DATE DEFAULT (DATE('now'))
    );
    """)

    # Admins
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Admins (
        admin_id      INTEGER PRIMARY KEY AUTOINCREMENT,
        adminname     TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name     TEXT,
        email         TEXT UNIQUE NOT NULL,
        created_at    DATE DEFAULT (DATE('now'))
    );
    """)

    # Restaurants
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Restaurants (
        restaurant_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name          TEXT NOT NULL,
        location      TEXT NOT NULL,
        cuisine       TEXT,
        rating        REAL CHECK (rating >= 0 AND rating <= 5),
        description   TEXT,
        opening_time  TEXT,
        closing_time  TEXT,
        created_at    DATE DEFAULT (DATE('now'))
    );
    """)

    # Tables
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Tables (
        table_id      INTEGER PRIMARY KEY AUTOINCREMENT,
        restaurant_id INTEGER NOT NULL,
        table_number  TEXT,
        capacity      INTEGER NOT NULL,
        FOREIGN KEY (restaurant_id) REFERENCES Restaurants(restaurant_id) ON DELETE CASCADE
    );
    """)

    # Reservations
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Reservations (
        reservation_id  INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id     INTEGER NOT NULL,
        restaurant_id   INTEGER NOT NULL,
        table_id        INTEGER,
        reservation_date DATE NOT NULL,
        reservation_time TEXT NOT NULL,
        guests          INTEGER NOT NULL CHECK (guests > 0),
        status          TEXT CHECK (status IN ('pending', 'confirmed', 'rejected', 'completed', 'cancelled')) DEFAULT 'pending',
        created_at      DATE DEFAULT (DATE('now')),
        FOREIGN KEY (customer_id) REFERENCES Customers(customer_id) ON DELETE CASCADE,
        FOREIGN KEY (restaurant_id) REFERENCES Restaurants(restaurant_id) ON DELETE CASCADE,
        FOREIGN KEY (table_id) REFERENCES Tables(table_id) ON DELETE SET NULL
    );
    """)

    # ReservationHistory
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ReservationHistory (
        history_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        reservation_id INTEGER NOT NULL,
        action         TEXT NOT NULL,
        action_by_admin INTEGER,
        action_by_customer INTEGER,
        action_time    DATE DEFAULT (DATE('now')),
        note           TEXT,
        FOREIGN KEY (reservation_id) REFERENCES Reservations(reservation_id) ON DELETE CASCADE,
        FOREIGN KEY (action_by_admin) REFERENCES Admins(admin_id) ON DELETE SET NULL,
        FOREIGN KEY (action_by_customer) REFERENCES Customers(customer_id) ON DELETE SET NULL
    );
    """)

    # --- BẮT ĐẦU THÊM DỮ LIỆU MẪU ---

    cur.execute("SELECT COUNT(*) FROM Admins;")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO Admins (adminname, password_hash, full_name, email) VALUES (?, ?, ?, ?);",
                    ("admin1", generate_password_hash("admin"), "Alice Admin", "admin01@example.com"))

    cur.execute("SELECT COUNT(*) FROM Customers;")
    if cur.fetchone()[0] == 0:
        cur.executemany("INSERT INTO Customers (username, password_hash, full_name, email, phone) VALUES (?, ?, ?, ?, ?);", [
            ("cuong", generate_password_hash("admin"), "John Doe", "john@example.com", "123456789"),
        ])
    
    cur.execute("SELECT COUNT(*) FROM Restaurants;")
    if cur.fetchone()[0] == 0:
        cur.executemany("INSERT INTO Restaurants (name, location, cuisine, rating, description, opening_time, closing_time) VALUES (?, ?, ?, ?, ?, ?, ?);", [
            # Dữ liệu cũ
            ("Pizza Palace", "New York, NY", "Italian", 4.5, "Authentic Italian pizza.", "11:00", "22:00"),
            ("Sushi World", "Los Angeles, CA", "Japanese", 4.7, "Fresh sushi and sashimi.", "12:00", "23:00"),
            # 5 nhà hàng mới
            ("The Golden Spoon", "Hanoi, Vietnam", "Vietnamese", 4.8, "Modern Vietnamese cuisine with a classic touch.", "10:00", "22:00"),
            ("Le Parisien Bistro", "Paris, France", "French", 4.6, "A cozy corner of Paris in your city.", "12:00", "23:00"),
            ("Taco Temple", "Mexico City, Mexico", "Mexican", 4.9, "The most authentic tacos you will ever taste.", "11:30", "21:30"),
            ("Bangkok Spice", "Bangkok, Thailand", "Thai", 4.7, "Experience the true flavors of Thailand.", "10:30", "22:30"),
            ("Burger Hub", "Chicago, IL", "American", 4.4, "Gourmet burgers and craft beers.", "11:00", "23:00"),
        ])

    cur.execute("SELECT COUNT(*) FROM Tables;")
    if cur.fetchone()[0] == 0:
        cur.executemany("INSERT INTO Tables (restaurant_id, table_number, capacity) VALUES (?, ?, ?);", [
            # Dữ liệu cũ
            (1, "T1", 2), (1, "T2", 4), (1, "T3", 6),
            (2, "T1", 2), (2, "T2", 4), (2, "T3", 6),
            # Dữ liệu 25 bàn mới
            (3, "V1", 2), (3, "V2", 2), (3, "V3", 4), (3, "V4", 6), (3, "V5", 8),
            (4, "P1", 2), (4, "P2", 2), (4, "P3", 4), (4, "P4", 4), (4, "P5", 6),
            (5, "M1", 4), (5, "M2", 4), (5, "M3", 6), (5, "M4", 6), (5, "M5", 10),
            (6, "B1", 2), (6, "B2", 4), (6, "B3", 4), (6, "B4", 5), (6, "B5", 7),
            (7, "H1", 2), (7, "H2", 3), (7, "H3", 4), (7, "H4", 6), (7, "H5", 6),
        ])

    db.commit()
    db.close()

if __name__ == '__main__':
    # Xóa file database cũ nếu có để tạo lại từ đầu
    import os
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Removed old database file: {DB_PATH}")
    
    init_db()