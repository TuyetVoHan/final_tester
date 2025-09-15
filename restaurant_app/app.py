from flask import Flask, render_template, request, redirect, url_for, flash, session, g
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
from datetime import datetime
import re
import psycopg2
import psycopg2.extras

app = Flask(__name__)
# Đảm bảo bạn đặt biến môi trường SECRET_KEY trên Render
app.secret_key = os.environ.get("SECRET_KEY", "a_default_secret_key_for_development")

# -----------------------
# DB Connection (PostgreSQL)
# -----------------------
def get_db():
    """Mở một kết nối mới tới cơ sở dữ liệu cho mỗi request."""
    if 'db' not in g:
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            raise RuntimeError("DATABASE_URL is not set.")
        g.db = psycopg2.connect(db_url)
    return g.db

@app.teardown_appcontext
def close_db(exc):
    """Đóng kết nối cơ sở dữ liệu khi request kết thúc."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

# -----------------------
# Helpers & decorators
# -----------------------
def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if 'user' not in session:
                flash("Please log in first.", "warning")
                return redirect(url_for('login'))
            if role == 'admin' and session.get('role') != 'admin':
                flash("Admin area. Access denied.", "danger")
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return wrapper
    return decorator

# -----------------------
# Public routes
# -----------------------
@app.route('/')
def index():
    return render_template('index.html')


# Register (customer)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        full_name = request.form.get('full_name', '')
        email = request.form['email'].strip()
        phone = request.form.get('phone', '').strip()

        error = False
        if len(username) < 4:
            flash('Username must be at least 4 characters long.', 'danger')
            error = True
        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'danger')
            error = True
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            error = True
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('Invalid email address.', 'danger')
            error = True
        if phone and not re.match(r"^\d{10}$", phone):
            flash('Invalid phone number. It must be 10 digits.', 'danger')
            error = True

        if error:
            return render_template('register.html',
                                   username=username,
                                   full_name=full_name,
                                   email=email,
                                   phone=phone)

        db = get_db()
        cur = db.cursor()
        try:
            cur.execute("INSERT INTO Customers (username, password_hash, full_name, email, phone) VALUES (%s, %s, %s, %s, %s);",
                       (username, generate_password_hash(password), full_name, email, phone))
            db.commit()
            flash('Account created. Please log in.', 'success')
            return redirect(url_for('login'))
        except psycopg2.IntegrityError:
            db.rollback()
            flash('Username or email already exists.', 'danger')
        finally:
            cur.close()

    return render_template('register.html')

# Login (customer or admin)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        who = request.form.get('who')
        username = request.form['username'].strip()
        password = request.form['password']

        db = get_db()
        cur = db.cursor(cursor_factory=psycopg2.extras.DictCursor)
        if who == 'admin':
            cur.execute("SELECT * FROM Admins WHERE adminname = %s;", (username,))
            row = cur.fetchone()
            if row and check_password_hash(row['password_hash'], password):
                session['user'] = row['admin_id']
                session['role'] = 'admin'
                session['name'] = row['full_name'] or row['adminname']
                flash('Admin logged in.', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Invalid admin credentials.', 'danger')
        else:
            cur.execute("SELECT * FROM Customers WHERE username = %s;", (username,))
            row = cur.fetchone()
            if row and check_password_hash(row['password_hash'], password):
                session['user'] = row['customer_id']
                session['role'] = 'customer'
                session['name'] = row['full_name'] or row['username']
                flash('Logged in.', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password.', 'danger')
        cur.close()

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.', 'info')
    return redirect(url_for('index'))

# Profile & change password
@app.route('/profile', methods=['GET', 'POST'])
@login_required(role='customer')
def profile():
    db = get_db()
    uid = session['user']

    if request.method == 'POST':
        full = request.form.get('full_name', '')
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()

        error = False
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('Invalid email address.', 'danger')
            error = True
        
        if phone and not re.match(r"^\d{10}$", phone):
            flash('Invalid phone number. It must be 10 digits.', 'danger')
            error = True
        
        if not error:
            cur = db.cursor()
            try:
                cur.execute("UPDATE Customers SET full_name = %s, email = %s, phone = %s WHERE customer_id = %s;",
                           (full, email, phone, uid))
                db.commit()
                flash('Profile updated.', 'success')
            except psycopg2.IntegrityError:
                db.rollback()
                flash('Email already in use by another account.', 'danger')
            finally:
                cur.close()

    cur = db.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM Customers WHERE customer_id = %s;", (uid,))
    user = cur.fetchone()
    cur.close()
    return render_template('profile.html', user=user)

@app.route('/change_password', methods=['GET', 'POST'])
@login_required(role='customer')
def change_password():
    db = get_db()
    uid = session['user']
    if request.method == 'POST':
        old = request.form['old_password']
        new = request.form['new_password']
        cur = db.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT password_hash FROM Customers WHERE customer_id = %s;", (uid,))
        row = cur.fetchone()
        cur.close()
        if not row or not check_password_hash(row['password_hash'], old):
            flash('Old password incorrect.', 'danger')
        else:
            cur = db.cursor()
            cur.execute("UPDATE Customers SET password_hash = %s WHERE customer_id = %s;",
                       (generate_password_hash(new), uid))
            db.commit()
            cur.close()
            flash('Password changed.', 'success')
            return redirect(url_for('profile'))
    return render_template('change_password.html')

# -----------------------
# Restaurant listing & search
# -----------------------
@app.route('/restaurants')
def restaurants():
    q_location = request.args.get('location', '').strip()
    q_cuisine = request.args.get('cuisine', '').strip()
    q_sort = request.args.get('sort', 'rating')

    sql = "SELECT * FROM Restaurants WHERE 1=1"
    params = []
    if q_location:
        sql += " AND location ILIKE %s" # ILIKE for case-insensitive search in PostgreSQL
        params.append(f"%{q_location}%")
    if q_cuisine:
        sql += " AND cuisine ILIKE %s"
        params.append(f"%{q_cuisine}%")
    if q_sort == 'rating':
        sql += " ORDER BY rating DESC"
    else:
        sql += " ORDER BY name ASC"

    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    return render_template('restaurants.html', restaurants=rows, q_location=q_location, q_cuisine=q_cuisine)

# Restaurant detail & reservation form
@app.route('/restaurant/<int:rid>', methods=['GET', 'POST'])
def restaurant_detail(rid):
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM Restaurants WHERE restaurant_id = %s", (rid,))
    restaurant = cur.fetchone()
    cur.close()
    if not restaurant:
        flash('Restaurant not found.', 'danger')
        return redirect(url_for('restaurants'))

    cur = db.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM Tables WHERE restaurant_id = %s ORDER BY capacity", (rid,))
    tables = cur.fetchall()
    cur.close()

    if request.method == 'POST':
        # ... (Phần code này giữ nguyên logic, chỉ thay đổi cách thực thi SQL)
        if 'role' not in session or session['role'] != 'customer':
            flash('Please login as a customer to make a reservation.', 'warning')
            return redirect(url_for('login'))

        customer_id = session['user']
        table_id = request.form.get('table_id')
        date = request.form['date']
        time = request.form['time']
        guests = int(request.form['guests'])

        # ... (Logic validation giữ nguyên)

        cur = db.cursor(cursor_factory=psycopg2.extras.DictCursor)
        if table_id:
            cur.execute("SELECT capacity FROM Tables WHERE table_id = %s AND restaurant_id = %s", (table_id, rid))
            t = cur.fetchone()
            # ... (Logic check capacity)
        else:
            cur.execute("""
                SELECT t.table_id, t.capacity FROM Tables t
                WHERE t.restaurant_id = %s AND t.capacity >= %s
                AND t.table_id NOT IN (
                    SELECT table_id FROM Reservations r
                    WHERE r.reservation_date = %s AND r.reservation_time = %s AND r.status IN ('pending', 'confirmed')
                )
                ORDER BY t.capacity ASC
                LIMIT 1
            """, (rid, guests, date, time))
            candidate = cur.fetchone()
            if candidate:
                table_id = candidate['table_id']
            else:
                flash('No available table for that time and party size.', 'danger')
                return redirect(url_for('restaurant_detail', rid=rid))

        cur.execute("""
            SELECT 1 FROM Reservations
            WHERE table_id = %s AND reservation_date = %s AND reservation_time = %s AND status IN ('pending','confirmed')
        """, (table_id, date, time))
        conflict = cur.fetchone()
        
        if conflict:
            flash('Selected table already booked for that time.', 'danger')
            return redirect(url_for('restaurant_detail', rid=rid))

        cur.execute("""
            INSERT INTO Reservations (customer_id, restaurant_id, table_id, reservation_date, reservation_time, guests, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING reservation_id
        """, (customer_id, rid, table_id, date, time, guests, 'pending'))
        rid_new = cur.fetchone()['reservation_id']
        
        cur.execute("""
            INSERT INTO ReservationHistory (reservation_id, action, action_by_customer, note)
            VALUES (%s, 'created', %s, %s)
        """, (rid_new, customer_id, 'Customer created reservation.'))
        
        db.commit()
        cur.close()

        flash('Reservation created and is pending confirmation.', 'success')
        return redirect(url_for('bookings'))

    return render_template('restaurant_detail.html', restaurant=restaurant, tables=tables)


# Customer bookings
@app.route('/bookings')
@login_required(role='customer')
def bookings():
    db = get_db()
    uid = session['user']
    cur = db.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""
        SELECT r.*, rest.name as restaurant_name, t.table_number
        FROM Reservations r
        JOIN Restaurants rest ON r.restaurant_id = rest.restaurant_id
        LEFT JOIN Tables t ON r.table_id = t.table_id
        WHERE r.customer_id = %s
        ORDER BY r.reservation_date DESC, r.reservation_time DESC
    """, (uid,))
    rows = cur.fetchall()
    cur.close()
    return render_template('bookings.html', bookings=rows)

# Modify or cancel reservation (customer)
@app.route('/reservation/<int:res_id>/edit', methods=['GET', 'POST'])
@login_required(role='customer')
def edit_reservation(res_id):
    db = get_db()
    uid = session['user']
    cur = db.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM Reservations WHERE reservation_id = %s AND customer_id = %s", (res_id, uid))
    res = cur.fetchone()
    cur.close()
    if not res:
        flash('Reservation not found or access denied.', 'danger')
        return redirect(url_for('bookings'))

    if request.method == 'POST':
        cur = db.cursor()
        if request.form.get('action') == 'cancel':
            cur.execute("UPDATE Reservations SET status = 'cancelled' WHERE reservation_id = %s", (res_id,))
            cur.execute("INSERT INTO ReservationHistory (reservation_id, action, action_by_customer, note) VALUES (%s, 'cancelled', %s, %s)",
                       (res_id, uid, 'Customer cancelled reservation'))
            db.commit()
            cur.close()
            flash('Reservation cancelled.', 'info')
            return redirect(url_for('bookings'))

        # ... (Logic cập nhật giữ nguyên, chỉ thay đổi cách thực thi SQL)
        date = request.form['date']
        time = request.form['time']
        guests = int(request.form['guests'])
        table_id = res['table_id'] # Giữ lại logic tìm bàn
        
        # ...
        
        cur.execute("UPDATE Reservations SET reservation_date = %s, reservation_time = %s, guests = %s, table_id = %s, status = 'pending' WHERE reservation_id = %s",
                   (date, time, guests, table_id, res_id))
        cur.execute("INSERT INTO ReservationHistory (reservation_id, action, action_by_customer, note) VALUES (%s, 'modified', %s, %s)",
                   (res_id, uid, 'Customer modified reservation'))
        db.commit()
        cur.close()
        flash('Reservation updated.', 'success')
        return redirect(url_for('bookings'))

    # GET
    cur = db.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT name FROM Restaurants WHERE restaurant_id = %s", (res['restaurant_id'],))
    rest_name = cur.fetchone()['name']
    cur.close()
    return render_template('restaurant_detail.html', restaurant={'restaurant_id': res['restaurant_id'], 'name': rest_name}, tables=[], reservation=res, edit_mode=True)

# -----------------------
# Admin routes
# -----------------------
@app.route('/admin')
@login_required(role='admin')
def admin_dashboard():
    return render_template('admin_dashboard.html')

# Admin: list restaurants
@app.route('/admin/restaurants')
@login_required(role='admin')
def admin_restaurants():
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM Restaurants ORDER BY name")
    rows = cur.fetchall()
    cur.close()
    return render_template('admin_restaurants.html', restaurants=rows)

# Admin: add or edit restaurant
@app.route('/admin/restaurant/new', methods=['GET', 'POST'])
@app.route('/admin/restaurant/<int:rid>/edit', methods=['GET', 'POST'])
@login_required(role='admin')
def admin_restaurant_form(rid=None):
    db = get_db()
    if request.method == 'POST':
        name = request.form['name']
        location = request.form['location']
        cuisine = request.form['cuisine']
        rating = float(request.form.get('rating') or 0)
        description = request.form.get('description', '')
        cur = db.cursor()
        if rid:
            cur.execute("UPDATE Restaurants SET name=%s, location=%s, cuisine=%s, rating=%s, description=%s WHERE restaurant_id=%s",
                       (name, location, cuisine, rating, description, rid))
            flash('Restaurant updated.', 'success')
        else:
            cur.execute("INSERT INTO Restaurants (name, location, cuisine, rating, description) VALUES (%s, %s, %s, %s, %s)",
                        (name, location, cuisine, rating, description))
            flash('Restaurant added.', 'success')
        db.commit()
        cur.close()
        return redirect(url_for('admin_restaurants'))

    restaurant = None
    if rid:
        cur = db.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT * FROM Restaurants WHERE restaurant_id = %s", (rid,))
        restaurant = cur.fetchone()
        cur.close()
    return render_template('admin_restaurant_form.html', restaurant=restaurant)

# Admin: delete
@app.route('/admin/restaurant/<int:rid>/delete', methods=['POST'])
@login_required(role='admin')
def admin_restaurant_delete(rid):
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM Restaurants WHERE restaurant_id = %s", (rid,))
    db.commit()
    cur.close()
    flash('Restaurant deleted.', 'info')
    return redirect(url_for('admin_restaurants'))

# Admin: manage reservations
@app.route('/admin/reservations')
@login_required(role='admin')
def admin_reservations():
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""
        SELECT r.*, c.username, rest.name as restaurant_name, t.table_number
        FROM Reservations r
        JOIN Customers c ON r.customer_id = c.customer_id
        JOIN Restaurants rest ON r.restaurant_id = rest.restaurant_id
        LEFT JOIN Tables t ON r.table_id = t.table_id
        ORDER BY r.reservation_date DESC, r.reservation_time DESC
    """)
    rows = cur.fetchall()
    cur.close()
    return render_template('admin_reservations.html', reservations=rows)

@app.route('/admin/reservation/<int:res_id>/update', methods=['POST'])
@login_required(role='admin')
def admin_update_reservation(res_id):
    new_status = request.form['status']
    admin_id = session['user']
    db = get_db()
    cur = db.cursor()
    cur.execute("UPDATE Reservations SET status = %s WHERE reservation_id = %s", (new_status, res_id))
    cur.execute("INSERT INTO ReservationHistory (reservation_id, action, action_by_admin, note) VALUES (%s, %s, %s, %s)",
               (res_id, f"status:{new_status}", admin_id, f"Admin set status to {new_status}"))
    db.commit()
    cur.close()
    flash('Reservation status updated.', 'success')
    return redirect(url_for('admin_reservations'))

# -----------------------
# Admin: Manage Users
# -----------------------
@app.route('/admin/users')
@login_required(role='admin')
def admin_manage_users():
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM Customers ORDER BY username ASC")
    users = cur.fetchall()
    cur.close()
    return render_template('admin_users.html', users=users)

@app.route('/admin/user/<int:uid>/edit', methods=['GET', 'POST'])
@login_required(role='admin')
def admin_edit_user(uid):
    db = get_db()
    if request.method == 'POST':
        full_name = request.form.get('full_name', '')
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()

        # ... (Validation logic giữ nguyên)
        
        cur = db.cursor()
        try:
            cur.execute("UPDATE Customers SET full_name = %s, email = %s, phone = %s WHERE customer_id = %s",
                       (full_name, email, phone, uid))
            db.commit()
            flash('User profile updated successfully.', 'success')
            return redirect(url_for('admin_manage_users'))
        except psycopg2.IntegrityError:
            db.rollback()
            flash('That email is already in use by another account.', 'danger')
        finally:
            cur.close()

    cur = db.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM Customers WHERE customer_id = %s", (uid,))
    user = cur.fetchone()
    cur.close()
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('admin_manage_users'))
    return render_template('admin_edit_user.html', user=user)

@app.route('/admin/user/<int:uid>/delete', methods=['POST'])
@login_required(role='admin')
def admin_delete_user(uid):
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM Customers WHERE customer_id = %s", (uid,))
    db.commit()
    cur.close()
    flash('User account has been deleted.', 'info')
    return redirect(url_for('admin_manage_users'))


@app.route('/init-db')
def init_db_command():
    """Tạo các bảng CSDL và chèn dữ liệu mẫu."""
    db = get_db()
    cur = db.cursor()

    # --- TẠO BẢNG ---
    # Chạy các lệnh CREATE TABLE từ file create_db.py, đã sửa cho PostgreSQL
    # Customers
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

    # Admins
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

    # Restaurants
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

    # Tables
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Tables (
        table_id      SERIAL PRIMARY KEY,
        restaurant_id INTEGER NOT NULL REFERENCES Restaurants(restaurant_id) ON DELETE CASCADE,
        table_number  TEXT,
        capacity      INTEGER NOT NULL
    );
    """)

    # Reservations
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
    
    # ReservationHistory
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
    
    print("✅ Các bảng đã được tạo thành công!")

    # --- CHÈN DỮ LIỆU MẪU ---
    # Chèn admin mặc định
    try:
        cur.execute("INSERT INTO Admins (adminname, password_hash, full_name, email) VALUES (%s, %s, %s, %s);",
                    ("admin01", generate_password_hash("adminpass"), "Alice Admin", "admin01@example.com"))
        print("✅ Admin mặc định đã được thêm.")
    except psycopg2.IntegrityError:
        db.rollback() # Bỏ qua nếu đã tồn tại
        print("ℹ️ Admin mặc định đã tồn tại.")

    # Chèn nhà hàng mẫu (từ file insert_data.py)
    try:
        restaurants = [
            ("Pizza Palace", "New York, NY", "Italian", 4.5, "Authentic Italian pizza with fresh ingredients."),
            ("Sushi World", "Los Angeles, CA", "Japanese", 4.7, "Fresh sushi and sashimi with modern twists."),
        ]
        cur.executemany("""
        INSERT INTO Restaurants (name, location, cuisine, rating, description)
        VALUES (%s, %s, %s, %s, %s)
        """, restaurants)
        print("✅ Dữ liệu nhà hàng mẫu đã được thêm.")
    except psycopg2.IntegrityError:
        db.rollback() # Bỏ qua nếu đã tồn tại
        print("ℹ️ Dữ liệu nhà hàng mẫu đã tồn tại.")

    db.commit()
    cur.close()
    
    flash("Database initialized successfully!", "success")
    return redirect(url_for('index'))
# -----------------------
# Run app
# -----------------------
if __name__ == '__main__':
    # Chạy server phát triển chỉ khi thực thi tệp này trực tiếp
    # Render sẽ sử dụng Gunicorn và không chạy khối này
    app.run(debug=True, port=5000)