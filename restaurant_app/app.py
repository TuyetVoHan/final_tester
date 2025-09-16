from flask import Flask, render_template, request, redirect, url_for, flash, session, g
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
from datetime import datetime
import re

DB_PATH = "restaurant_reservation.db"

app = Flask(__name__)
app.secret_key = "replace_with_a_secure_secret"  # change in production


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON;")
    return g.db

@app.teardown_appcontext
def close_db(exc):
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

        # --- BẮT ĐẦU VALIDATION ---
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
        
        # --- THÊM VALIDATE CHO SỐ ĐIỆN THOẠI ---
        if phone and not re.match(r"^\d{10}$", phone):
            flash('Invalid phone number. It must be 10 digits.', 'danger')
            error = True
        # --- KẾT THÚC VALIDATE SỐ ĐIỆN THOẠI ---

        if error:
            # Nếu có lỗi, render lại trang register và giữ lại dữ liệu người dùng đã nhập
            return render_template('register.html',
                                   username=username,
                                   full_name=full_name,
                                   email=email,
                                   phone=phone)
        # --- KẾT THÚC VALIDATION ---

        db = get_db()
        try:
            db.execute("INSERT INTO Customers (username, password_hash, full_name, email, phone) VALUES (?, ?, ?, ?, ?);",
                       (username, generate_password_hash(password), full_name, email, phone))
            db.commit()
            flash('Account created. Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError as e:
            flash('Username or email already exists.', 'danger')

    return render_template('register.html')

# Login (customer or admin)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        who = request.form.get('who')  # 'customer' or 'admin'
        username = request.form['username'].strip()
        password = request.form['password']

        db = get_db()
        if who == 'admin':
            cur = db.execute("SELECT * FROM Admins WHERE adminname = ?;", (username,))
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
            cur = db.execute("SELECT * FROM Customers WHERE username = ?;", (username,))
            row = cur.fetchone()
            if row and check_password_hash(row['password_hash'], password):
                session['user'] = row['customer_id']
                session['role'] = 'customer'
                session['name'] = row['full_name'] or row['username']
                flash('Logged in.', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password.', 'danger')

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

        # --- BẮT ĐẦU VALIDATION ---
        error = False
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('Invalid email address.', 'danger')
            error = True
        
        if phone and not re.match(r"^\d{10}$", phone):
            flash('Invalid phone number. It must be 10 digits.', 'danger')
            error = True
        
        if not error:
            # Chỉ cập nhật DB nếu không có lỗi
            try:
                db.execute("UPDATE Customers SET full_name = ?, email = ?, phone = ? WHERE customer_id = ?;",
                           (full, email, phone, uid))
                db.commit()
                flash('Profile updated.', 'success')
            except sqlite3.IntegrityError:
                flash('Email already in use by another account.', 'danger')
        # --- KẾT THÚC VALIDATION ---

    # Lấy thông tin người dùng để hiển thị
    cur = db.execute("SELECT * FROM Customers WHERE customer_id = ?;", (uid,))
    user = cur.fetchone()
    return render_template('profile.html', user=user)

@app.route('/change_password', methods=['GET', 'POST'])
@login_required(role='customer')
def change_password():
    db = get_db()
    uid = session['user']
    if request.method == 'POST':
        old = request.form['old_password']
        new = request.form['new_password']
        cur = db.execute("SELECT password_hash FROM Customers WHERE customer_id = ?;", (uid,))
        row = cur.fetchone()
        if not row or not check_password_hash(row['password_hash'], old):
            flash('Old password incorrect.', 'danger')
        else:
            db.execute("UPDATE Customers SET password_hash = ? WHERE customer_id = ?;",
                       (generate_password_hash(new), uid))
            db.commit()
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
    q_sort = request.args.get('sort', 'rating')  # rating or name

    sql = "SELECT * FROM Restaurants WHERE 1=1"
    params = []
    if q_location:
        sql += " AND location LIKE ?"
        params.append(f"%{q_location}%")
    if q_cuisine:
        sql += " AND cuisine LIKE ?"
        params.append(f"%{q_cuisine}%")
    if q_sort == 'rating':
        sql += " ORDER BY rating DESC"
    else:
        sql += " ORDER BY name ASC"

    db = get_db()
    cur = db.execute(sql, params)
    rows = cur.fetchall()
    return render_template('restaurants.html', restaurants=rows, q_location=q_location, q_cuisine=q_cuisine)

def is_reservation_date_valid(date_str):
    """Kiểm tra xem ngày đặt bàn có hợp lệ không (không phải quá khứ)."""
    return date_str >= datetime.now().strftime('%Y-%m-%d')

def is_reservation_time_valid(time_str, restaurant):
    """Kiểm tra xem thời gian đặt có nằm trong giờ mở cửa của nhà hàng không."""
    opening_time = restaurant['opening_time']
    closing_time = restaurant['closing_time']
    if opening_time and closing_time:
        return opening_time <= time_str < closing_time
    return True # Nếu nhà hàng không set giờ, coi như luôn hợp lệ

def find_available_table(db, rid, date, time, guests, selected_table_id=None):
    """Tìm một bàn trống phù hợp, ưu tiên bàn do người dùng chọn."""
    if selected_table_id:
        # Kiểm tra xem bàn người dùng chọn có còn trống không
        is_available = db.execute("""
            SELECT table_id FROM Tables
            WHERE table_id = ? AND capacity >= ? AND table_id NOT IN (
                SELECT r.table_id FROM Reservations r
                WHERE r.table_id IS NOT NULL AND r.reservation_date = ?
                AND r.status IN ('pending', 'confirmed')
                AND STRFTIME('%H:%M', r.reservation_time, '+2 hours') > ?
                AND r.reservation_time < STRFTIME('%H:%M', ?, '+2 hours')
            )
        """, (selected_table_id, guests, date, time, time)).fetchone()
        if is_available:
            return is_available['table_id']
        else:
            return None # Bàn đã chọn không hợp lệ hoặc không đủ chỗ
    else:
        # Tự động tìm bàn nhỏ nhất phù hợp
        available_table = db.execute("""
            SELECT t.table_id FROM Tables t
            WHERE t.restaurant_id = ? AND t.capacity >= ? AND t.table_id NOT IN (
                SELECT r.table_id FROM Reservations r
                WHERE r.table_id IS NOT NULL AND r.reservation_date = ?
                AND r.status IN ('pending', 'confirmed')
                AND STRFTIME('%H:%M', r.reservation_time, '+2 hours') > ?
                AND r.reservation_time < STRFTIME('%H:%M', ?, '+2 hours')
            )
            ORDER BY t.capacity ASC LIMIT 1
        """, (rid, guests, date, time, time)).fetchone()
        return available_table['table_id'] if available_table else None

# Restaurant detail & reservation form
@app.route('/restaurant/<int:rid>', methods=['GET', 'POST'])
def restaurant_detail(rid):
    db = get_db()
    restaurant = db.execute("SELECT * FROM Restaurants WHERE restaurant_id = ?", (rid,)).fetchone()
    if not restaurant:
        flash('Restaurant not found.', 'danger')
        return redirect(url_for('restaurants'))

    if request.method == 'POST':
        if 'role' not in session or session['role'] != 'customer':
            flash('Please login as a customer to make a reservation.', 'warning')
            return redirect(url_for('login'))

        # --- Lấy dữ liệu từ form ---
        date = request.form['date']
        time = request.form['time']
        guests = int(request.form['guests'])
        selected_table_id = request.form.get('table_id')

        # --- Gọi các hàm kiểm tra riêng biệt ---
        if not is_reservation_date_valid(date):
            flash("You cannot make a reservation for a past date.", 'danger')
            return redirect(url_for('restaurant_detail', rid=rid))

        if not is_reservation_time_valid(time, restaurant):
            flash(f"Sorry, the restaurant is only open from {restaurant['opening_time']} to {restaurant['closing_time']}.", 'danger')
            return redirect(url_for('restaurant_detail', rid=rid))

        assigned_table_id = find_available_table(db, rid, date, time, guests, selected_table_id)

        # --- Xử lý kết quả ---
        if not assigned_table_id:
            flash('No available table for that time and party size. Please try another time or select a different table.', 'danger')
            return redirect(url_for('restaurant_detail', rid=rid))

        # --- Lưu vào CSDL nếu mọi thứ hợp lệ ---
        customer_id = session['user']
        cur = db.execute("""
            INSERT INTO Reservations (customer_id, restaurant_id, table_id, reservation_date, reservation_time, guests, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (customer_id, rid, assigned_table_id, date, time, guests, 'pending'))
        db.commit()
        
        flash('Reservation created and is pending confirmation.', 'success')
        return redirect(url_for('bookings'))

    # --- Xử lý cho GET request ---
    today_date = datetime.now().strftime('%Y-%m-%d')
    tables = db.execute("SELECT * FROM Tables WHERE restaurant_id = ?", (rid,)).fetchall()
    return render_template('restaurant_detail.html', restaurant=restaurant, tables=tables, today_date=today_date)

# Customer bookings
@app.route('/bookings')
@login_required(role='customer')
def bookings():
    db = get_db()
    uid = session['user']
    cur = db.execute("""
        SELECT r.*, rest.name as restaurant_name, t.table_number
        FROM Reservations r
        JOIN Restaurants rest ON r.restaurant_id = rest.restaurant_id
        LEFT JOIN Tables t ON r.table_id = t.table_id
        WHERE r.customer_id = ?
        ORDER BY r.reservation_date DESC, r.reservation_time DESC
    """, (uid,))
    rows = cur.fetchall()
    return render_template('bookings.html', bookings=rows)

# Modify or cancel reservation (customer)
@app.route('/reservation/<int:res_id>/edit', methods=['GET', 'POST'])
@login_required(role='customer')
def edit_reservation(res_id):
    db = get_db()
    uid = session['user']
    cur = db.execute("SELECT * FROM Reservations WHERE reservation_id = ? AND customer_id = ?", (res_id, uid))
    res = cur.fetchone()
    if not res:
        flash('Reservation not found or access denied.', 'danger')
        return redirect(url_for('bookings'))

    if request.method == 'POST':
        if request.form.get('action') == 'cancel':
            db.execute("UPDATE Reservations SET status = 'cancelled' WHERE reservation_id = ?", (res_id,))
            db.execute("INSERT INTO ReservationHistory (reservation_id, action, action_by_customer, note) VALUES (?, 'cancelled', ?, ?)",
                       (res_id, uid, 'Customer cancelled reservation'))
            db.commit()
            flash('Reservation cancelled.', 'info')
            return redirect(url_for('bookings'))

        date = request.form['date']
        time = request.form['time']
        guests = int(request.form['guests'])

        # --- BẮT ĐẦU VALIDATION NGÀY THÁNG ---
        if date < datetime.now().strftime('%Y-%m-%d'):
            flash("You cannot move a reservation to a past date.", 'danger')
            return redirect(url_for('edit_reservation', res_id=res_id))
        # --- KẾT THÚC VALIDATION NGÀY THÁNG ---

        table_id = res['table_id']
        if table_id:
            cap = db.execute("SELECT capacity FROM Tables WHERE table_id = ?", (table_id,)).fetchone()['capacity']
            if guests > cap:
                table_id = None

        if not table_id:
            candidate = db.execute("""
                SELECT t.table_id FROM Tables t
                WHERE t.restaurant_id = ? AND t.capacity >= ?
                AND t.table_id NOT IN (
                    SELECT table_id FROM Reservations r
                    WHERE r.reservation_date = ? AND r.reservation_time = ? AND r.status IN ('pending','confirmed') AND r.reservation_id != ?
                )
                ORDER BY t.capacity ASC
                LIMIT 1
            """, (res['restaurant_id'], guests, date, time, res_id)).fetchone()
            if candidate:
                table_id = candidate['table_id']
            else:
                flash('No available table for updated time/party size.', 'danger')
                return redirect(url_for('edit_reservation', res_id=res_id))

        db.execute("UPDATE Reservations SET reservation_date = ?, reservation_time = ?, guests = ?, table_id = ?, status = 'pending' WHERE reservation_id = ?",
                   (date, time, guests, table_id, res_id))
        db.execute("INSERT INTO ReservationHistory (reservation_id, action, action_by_customer, note) VALUES (?, 'modified', ?, ?)",
                   (res_id, uid, 'Customer modified reservation'))
        db.commit()
        flash('Reservation updated.', 'success')
        return redirect(url_for('bookings'))

    # GET: Lấy ngày hiện tại để truyền ra template
    today_date = datetime.now().strftime('%Y-%m-%d')
    rest_name = db.execute("SELECT name FROM Restaurants WHERE restaurant_id = ?", (res['restaurant_id'],)).fetchone()['name']
    return render_template('restaurant_detail.html', restaurant={'restaurant_id': res['restaurant_id'], 'name': rest_name}, tables=[], reservation=res, edit_mode=True, today_date=today_date)
# -----------------------
# Admin routes
# -----------------------
@app.route('/admin')
@login_required(role='admin')
def admin_dashboard():
    db = get_db()

    # Thống kê số lượt đặt bàn mới trong ngày
    new_bookings_today = db.execute(
        "SELECT COUNT(*) as count FROM Reservations WHERE DATE(created_at) = DATE('now')"
    ).fetchone()['count']

    # Thống kê tổng số khách hàng
    total_customers = db.execute(
        "SELECT COUNT(*) as count FROM Customers"
    ).fetchone()['count']
    
    # Thống kê tổng số nhà hàng
    total_restaurants = db.execute(
        "SELECT COUNT(*) as count FROM Restaurants"
    ).fetchone()['count']

    # Top 5 nhà hàng được đặt nhiều nhất
    top_restaurants = db.execute("""
        SELECT r.name, COUNT(res.reservation_id) as booking_count
        FROM Restaurants r
        LEFT JOIN Reservations res ON r.restaurant_id = res.restaurant_id
        GROUP BY r.restaurant_id
        ORDER BY booking_count DESC
        LIMIT 5
    """).fetchall()

    stats = {
        'new_bookings_today': new_bookings_today,
        'total_customers': total_customers,
        'total_restaurants': total_restaurants,
        'top_restaurants': top_restaurants
    }

    return render_template('admin_dashboard.html', stats=stats)

# Admin: list restaurants
@app.route('/admin/restaurants')
@login_required(role='admin')
def admin_restaurants():
    db = get_db()
    rows = db.execute("SELECT * FROM Restaurants ORDER BY name").fetchall()
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
        opening_time = request.form.get('opening_time') # THÊM DÒNG NÀY
        closing_time = request.form.get('closing_time') # THÊM DÒNG NÀY

        if rid:
            db.execute("UPDATE Restaurants SET name=?, location=?, cuisine=?, rating=?, description=?, opening_time=?, closing_time=? WHERE restaurant_id=?",
                       (name, location, cuisine, rating, description, opening_time, closing_time, rid)) # CẬP NHẬT CÂU LỆNH
            flash('Restaurant updated.', 'success')
        else:
            cur = db.execute("INSERT INTO Restaurants (name, location, cuisine, rating, description, opening_time, closing_time) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (name, location, cuisine, rating, description, opening_time, closing_time)) # CẬP NHẬT CÂU LỆNH
            rid = cur.lastrowid
            flash('Restaurant added.', 'success')
        db.commit()
        return redirect(url_for('admin_restaurants'))

    restaurant = None
    if rid:
        restaurant = db.execute("SELECT * FROM Restaurants WHERE restaurant_id = ?", (rid,)).fetchone()
    return render_template('admin_restaurant_form.html', restaurant=restaurant)
# Admin: delete
@app.route('/admin/restaurant/<int:rid>/delete', methods=['POST'])
@login_required(role='admin')
def admin_restaurant_delete(rid):
    db = get_db()
    db.execute("DELETE FROM Restaurants WHERE restaurant_id = ?", (rid,))
    db.commit()
    flash('Restaurant deleted.', 'info')
    return redirect(url_for('admin_restaurants'))

# Admin: manage reservations
@app.route('/admin/reservations')
@login_required(role='admin')
def admin_reservations():
    db = get_db()
    rows = db.execute("""
        SELECT r.*, c.username, rest.name as restaurant_name, t.table_number
        FROM Reservations r
        JOIN Customers c ON r.customer_id = c.customer_id
        JOIN Restaurants rest ON r.restaurant_id = rest.restaurant_id
        LEFT JOIN Tables t ON r.table_id = t.table_id
        ORDER BY r.reservation_date DESC, r.reservation_time DESC
    """).fetchall()
    return render_template('admin_reservations.html', reservations=rows)

@app.route('/admin/reservation/<int:res_id>/update', methods=['POST'])
@login_required(role='admin')
def admin_update_reservation(res_id):
    new_status = request.form['status']
    admin_id = session['user']
    db = get_db()
    db.execute("UPDATE Reservations SET status = ? WHERE reservation_id = ?", (new_status, res_id))
    db.execute("INSERT INTO ReservationHistory (reservation_id, action, action_by_admin, note) VALUES (?, ?, ?, ?)",
               (res_id, f"status:{new_status}", admin_id, f"Admin set status to {new_status}"))
    db.commit()
    flash('Reservation status updated.', 'success')
    return redirect(url_for('admin_reservations'))

# # Admin: manage users (simple listing)
# @app.route('/admin/users')
# @login_required(role='admin')
# def admin_users():
#     db = get_db()
#     users = db.execute("SELECT * FROM Customers ORDER BY created_at DESC").fetchall()
#     return render_template('admin_restaurants.html', restaurants=[], users=users)  # reuse simple template or create new one

# -----------------------
# Admin: Manage Users
# -----------------------
@app.route('/admin/users')
@login_required(role='admin')
def admin_manage_users():
    db = get_db()
    users = db.execute("SELECT * FROM Customers ORDER BY username ASC").fetchall()
    return render_template('admin_users.html', users=users)

@app.route('/admin/user/<int:uid>/edit', methods=['GET', 'POST'])
@login_required(role='admin')
def admin_edit_user(uid):
    db = get_db()
    if request.method == 'POST':
        full_name = request.form.get('full_name', '')
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()

        # Validation
        error = False
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('Invalid email address.', 'danger')
            error = True
        if phone and not re.match(r"^\d{10}$", phone):
            flash('Invalid phone number. It must be 10 digits.', 'danger')
            error = True
        
        if not error:
            try:
                db.execute("UPDATE Customers SET full_name = ?, email = ?, phone = ? WHERE customer_id = ?",
                           (full_name, email, phone, uid))
                db.commit()
                flash('User profile updated successfully.', 'success')
                return redirect(url_for('admin_manage_users'))
            except sqlite3.IntegrityError:
                flash('That email is already in use by another account.', 'danger')

    # For GET request or if there was an error
    user = db.execute("SELECT * FROM Customers WHERE customer_id = ?", (uid,)).fetchone()
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('admin_manage_users'))
    return render_template('admin_edit_user.html', user=user)

@app.route('/admin/user/<int:uid>/delete', methods=['POST'])
@login_required(role='admin')
def admin_delete_user(uid):
    db = get_db()
    # Optional: Check if the user is not deleting themselves, although admin accounts are separate.
    # This is a good practice.
    db.execute("DELETE FROM Customers WHERE customer_id = ?", (uid,))
    db.commit()
    flash('User account has been deleted.', 'info')
    return redirect(url_for('admin_manage_users'))

# -----------------------
# Admin: Manage Tables
# -----------------------
@app.route('/admin/restaurant/<int:rid>/tables', methods=['GET', 'POST'])
@login_required(role='admin')
def admin_manage_tables(rid):
    db = get_db()
    
    # Lấy thông tin nhà hàng để hiển thị tên
    restaurant = db.execute("SELECT * FROM Restaurants WHERE restaurant_id = ?", (rid,)).fetchone()
    if not restaurant:
        flash('Restaurant not found.', 'danger')
        return redirect(url_for('admin_restaurants'))

    # Xử lý khi admin thêm bàn mới
    if request.method == 'POST':
        table_number = request.form['table_number']
        capacity = int(request.form['capacity'])
        
        if not table_number or capacity <= 0:
            flash('Table number and capacity are required.', 'danger')
        else:
            db.execute("INSERT INTO Tables (restaurant_id, table_number, capacity) VALUES (?, ?, ?)",
                       (rid, table_number, capacity))
            db.commit()
            flash('New table added successfully.', 'success')
        
        return redirect(url_for('admin_manage_tables', rid=rid))

    # Lấy danh sách các bàn hiện có của nhà hàng
    tables = db.execute("SELECT * FROM Tables WHERE restaurant_id = ? ORDER BY table_number", (rid,)).fetchall()
    
    return render_template('admin_manage_tables.html', tables=tables, restaurant=restaurant)

@app.route('/admin/table/<int:tid>/delete', methods=['POST'])
@login_required(role='admin')
def admin_delete_table(tid):
    db = get_db()
    
    # Lấy restaurant_id để redirect lại đúng trang
    table = db.execute("SELECT restaurant_id FROM Tables WHERE table_id = ?", (tid,)).fetchone()
    if table:
        db.execute("DELETE FROM Tables WHERE table_id = ?", (tid,))
        db.commit()
        flash('Table deleted.', 'info')
        return redirect(url_for('admin_manage_tables', rid=table['restaurant_id']))
    
    flash('Table not found.', 'danger')
    return redirect(url_for('admin_restaurants'))


# -----------------------
# Run app
# -----------------------
if __name__ == '__main__':
    app.run(debug=True, port=5000)
