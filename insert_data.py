import sqlite3

def insert_sample_data():
    conn = sqlite3.connect("restaurant_reservation.db")
    cursor = conn.cursor()

    # --------------------------
    # Insert Admin
    # --------------------------
    cursor.execute("""
    INSERT INTO Admins (adminname, password_hash, full_name, email)
    VALUES 
        ('admin01', 'hashed_pw_admin', 'Alice Admin', 'admin01@example.com')
    """)

    # --------------------------
    # Insert Customers
    # --------------------------
    cursor.executemany("""
    INSERT INTO Customers (username, password_hash, full_name, email, phone)
    VALUES (?, ?, ?, ?, ?)
    """, [
        ("john_doe", "hashed_pw_john", "John Doe", "john@example.com", "123456789"),
        ("jane_smith", "hashed_pw_jane", "Jane Smith", "jane@example.com", "987654321")
    ])

    # --------------------------
    # Insert Restaurants
    # --------------------------
    cursor.executemany("""
    INSERT INTO Restaurants (name, location, cuisine, rating, description)
    VALUES (?, ?, ?, ?, ?)
    """, [
        ("Pizza Palace", "New York, NY", "Italian", 4.5, "Authentic Italian pizza with fresh ingredients."),
        ("Sushi World", "Los Angeles, CA", "Japanese", 4.7, "Fresh sushi and sashimi with modern twists.")
    ])

    # --------------------------
    # Insert Tables
    # --------------------------
    cursor.executemany("""
    INSERT INTO Tables (restaurant_id, table_number, capacity)
    VALUES (?, ?, ?)
    """, [
        (1, "T1", 2),
        (1, "T2", 4),
        (1, "T3", 6),
        (2, "T1", 2),
        (2, "T2", 4),
        (2, "T3", 6)
    ])

    # --------------------------
    # Insert Reservations
    # --------------------------
    cursor.executemany("""
    INSERT INTO Reservations (customer_id, restaurant_id, table_id, reservation_date, reservation_time, guests, status)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, [
        (1, 1, 2, "2025-09-10", "19:00", 4, "pending"),     # John Doe at Pizza Palace
        (2, 2, 5, "2025-09-12", "18:30", 2, "confirmed")   # Jane Smith at Sushi World
    ])

    # --------------------------
    # Insert Reservation History
    # --------------------------
    cursor.executemany("""
    INSERT INTO ReservationHistory (reservation_id, action, action_by_customer, action_by_admin, note)
    VALUES (?, ?, ?, ?, ?)
    """, [
        (1, "created", 1, None, "John created a reservation at Pizza Palace."),
        (2, "created", 2, None, "Jane created a reservation at Sushi World."),
        (2, "confirmed", None, 1, "Admin confirmed Jane's reservation.")
    ])

    conn.commit()
    conn.close()
    print("✅ Sample data inserted successfully!")

if __name__ == "__main__":
    insert_sample_data()
