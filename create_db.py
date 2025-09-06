import sqlite3

def create_database():
    conn = sqlite3.connect("restaurant_reservation.db")
    cursor = conn.cursor()

    # ==========================
    # 1. CUSTOMERS
    # ==========================
    cursor.execute("""
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

    # ==========================
    # 2. ADMINS
    # ==========================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Admins (
        admin_id      INTEGER PRIMARY KEY AUTOINCREMENT,
        adminname     TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name     TEXT,
        email         TEXT UNIQUE NOT NULL,
        created_at    DATE DEFAULT (DATE('now'))
    );
    """)

    # ==========================
    # 3. RESTAURANTS
    # ==========================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Restaurants (
        restaurant_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name          TEXT NOT NULL,
        location      TEXT NOT NULL,
        cuisine       TEXT,
        rating        REAL CHECK (rating >= 0 AND rating <= 5),
        description   TEXT,
        created_at    DATE DEFAULT (DATE('now'))
    );
    """)

    # ==========================
    # 4. TABLES (per restaurant)
    # ==========================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Tables (
        table_id      INTEGER PRIMARY KEY AUTOINCREMENT,
        restaurant_id INTEGER NOT NULL,
        table_number  TEXT,
        capacity      INTEGER NOT NULL,
        FOREIGN KEY (restaurant_id) REFERENCES Restaurants(restaurant_id) ON DELETE CASCADE
    );
    """)

    # ==========================
    # 5. RESERVATIONS
    # ==========================
    cursor.execute("""
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

    # ==========================
    # 6. RESERVATION HISTORY
    # ==========================
    cursor.execute("""
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

    conn.commit()
    conn.close()
    print("✅ Database with DATE fields created successfully!")

if __name__ == "__main__":
    create_database()
