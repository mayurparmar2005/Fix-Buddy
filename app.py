from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response, jsonify
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import date, datetime, timedelta
import os
import re
import csv
import io
import secrets
import threading
import hashlib
import hmac
try:
    import razorpay
except ImportError:
    razorpay = None  # pip install razorpay if missing
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed; will use .env values

app = Flask(__name__)

# ========================
# ASYNC EMAIL HELPER
# ========================
def send_booking_email_async(recipient, services, total, address, date, time):
    """Build and send booking confirmation email in a background thread."""
    def _send():
        with app.app_context():
            try:
                msg = Message("Booking Confirmed - Fix Buddy", recipients=[recipient])
                msg.html = render_template(
                    "email_receipt.html",
                    services=services, total=total,
                    address=address, date=date, time=time
                )
                mail.send(msg)
                print("[Email] Booking confirmation sent to", recipient)
            except Exception as e:
                print(f"[Email] Failed: {e}")
    t = threading.Thread(target=_send, daemon=True)
    t.start()

def send_reset_email_async(recipient, name, reset_link):
    """Build and send password reset email in a background thread."""
    def _send():
        with app.app_context():
            try:
                msg = Message("Reset Your Fix Buddy Password", recipients=[recipient])
                msg.html = f"""
                <div style="font-family:Inter,sans-serif;max-width:480px;margin:auto;padding:30px;">
                    <h2 style="color:#4CAF50;">Fix Buddy Password Reset</h2>
                    <p>Hi <b>{name}</b>, we received a request to reset your password.</p>
                    <p>Click the button below within <b>1 hour</b>:</p>
                    <a href="{reset_link}" style="display:inline-block;background:#4CAF50;color:white;
                       padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:700;margin:16px 0;">
                        Reset Password
                    </a>
                    <p style="color:#999;font-size:12px;">If you didn't request this, ignore this email.</p>
                    <p style="color:#999;font-size:12px;">Link expires in 1 hour.</p>
                </div>
                """
                mail.send(msg)
                print("[Email] Password reset sent to", recipient)
            except Exception as e:
                print(f"[Email] Reset failed: {e}")
    t = threading.Thread(target=_send, daemon=True)
    t.start()

# Require a real secret key — never use the default in production
_secret_key = os.getenv("SECRET_KEY")
if not _secret_key or _secret_key == "super_secure_random_key":
    import warnings
    warnings.warn("[Security] SECRET_KEY is not set or is using the default value. Set a strong SECRET_KEY in .env!", stacklevel=2)
app.secret_key = _secret_key or "super_secure_random_key"

# ========================
# SECURE SESSION CONFIGURATION
# ========================
app.config['SESSION_COOKIE_HTTPONLY'] = True       # JS cannot read session cookie
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'      # Mitigate CSRF via cookie policy
app.config['SESSION_COOKIE_SECURE']   = False       # Set True in production (HTTPS only)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)

# ========================
# CSRF PROTECTION
# ========================
csrf = CSRFProtect(app)

# ========================
# RATE LIMITING
# ========================
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://"
)

# ========================
# EMAIL CONFIGURATION
# ========================
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME", "fixbuddy04@gmail.com")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")  # Must be set in .env
app.config['MAIL_DEFAULT_SENDER'] = os.getenv("MAIL_DEFAULT_SENDER", "fixbuddy04@gmail.com")
app.config['MAIL_TIMEOUT'] = 5   # kill SMTP if it takes > 5 seconds

if not app.config['MAIL_PASSWORD']:
    import warnings
    warnings.warn("[Security] MAIL_PASSWORD is not set in .env — email sending will fail.", stacklevel=2)

mail = Mail(app)

# ========================
# AUTO-MIGRATION: add transaction_id to payments if missing
# ========================
def run_migrations():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "fix_buddy")
        )
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.columns
            WHERE table_schema = DATABASE()
              AND table_name = 'payments'
              AND column_name = 'transaction_id'
        """)
        if cursor.fetchone()[0] == 0:
            cursor.execute("ALTER TABLE payments ADD COLUMN transaction_id VARCHAR(100) DEFAULT NULL")
            conn.commit()
            print("[DB] Migration: added transaction_id column to payments.")
        conn.close()
    except Exception as e:
        print(f"[DB] Migration error (non-fatal): {e}")

with app.app_context():
    run_migrations()

# ========================
# SECURITY HEADERS
# ========================
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options']  = 'nosniff'
    response.headers['X-Frame-Options']          = 'SAMEORIGIN'
    response.headers['X-XSS-Protection']         = '1; mode=block'
    response.headers['Referrer-Policy']           = 'strict-origin-when-cross-origin'
    return response

# ========================
# DATABASE CONNECTION
# ========================
def get_db_connection():
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "fix_buddy")
    )
    return conn

# ========================
# HOME / LOGIN
# ========================
@app.route("/", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        password_ok = False
        if user:
            stored = user["password"]
            if stored.startswith('pbkdf2:') or stored.startswith('scrypt:'):
                password_ok = check_password_hash(stored, password)
            else:
                # Legacy plain-text — accept and upgrade immediately
                password_ok = (stored == password)
                if password_ok:
                    cursor.execute(
                        "UPDATE users SET password=%s WHERE id=%s",
                        (generate_password_hash(password, method='pbkdf2:sha256'), user['id'])
                    )
                    conn.commit()

        conn.close()

        if password_ok:
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            return redirect(url_for("services_page"))
        else:
            flash("Invalid email or password!", "error")
            return redirect(url_for("login"))

    return render_template("index.html")

# ========================
# ADMIN LOGIN
# ========================
@app.route('/admin-login', methods=['GET', 'POST'])
@limiter.limit("5 per minute", methods=["POST"])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        admin_user = os.getenv("ADMIN_USERNAME", "admin")
        admin_pass = os.getenv("ADMIN_PASSWORD", "admin123")

        if username == admin_user and password == admin_pass:
            session['user_id'] = 'ADMIN'
            session['role'] = 'admin'
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid Admin Credentials", "error")
            return redirect(url_for('admin_login'))

    return render_template('admin_login.html')

# ========================
# EMPLOYEE LOGIN
# ========================
@app.route('/employee-login', methods=['GET', 'POST'])
@limiter.limit("10 per minute", methods=["POST"])
def employee_login():
    if 'user_id' in session and session.get('role') == 'professional':
        return redirect(url_for('employee_dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM professionals WHERE email = %s", (email,))
        user = cursor.fetchone()
        conn.close()

        password_ok = False
        if user:
            stored = user['password']
            if stored.startswith('pbkdf2:') or stored.startswith('scrypt:'):
                password_ok = check_password_hash(stored, password)
            else:
                password_ok = (stored == password)
                if password_ok:
                    conn2 = get_db_connection()
                    c2 = conn2.cursor()
                    c2.execute("UPDATE professionals SET password=%s WHERE id=%s",
                               (generate_password_hash(password, method='pbkdf2:sha256'), user['id']))
                    conn2.commit()
                    conn2.close()

        if password_ok:
            session['user_id'] = user['id']
            session['name'] = user['name']
            session['role'] = 'professional'
            flash('Login successful!', 'success')
            return redirect(url_for('employee_dashboard'))
        else:
            flash('Invalid Email or Password', 'error')

    return render_template('employee_login.html')

# ========================
# EMPLOYEE REGISTER
# ========================
@app.route('/employee-register', methods=['GET', 'POST'])
def employee_register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        service_type = request.form['service_type']
        experience = request.form.get('experience', 0)
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM professionals WHERE email = %s", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash("Email already registered. Please login.", "error")
            conn.close()
            return redirect(url_for('employee_login'))

        cursor.execute("""
            INSERT INTO professionals (name, email, phone, service_type, experience, password)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (name, email, phone, service_type, experience, hashed_password))
        conn.commit()
        conn.close()
        flash("Registration successful! Please login.", "success")
        return redirect(url_for('employee_login'))

    return render_template('employee_register.html')

# ========================
# EMPLOYEE DASHBOARD
# ========================
@app.route('/employee-dashboard')
def employee_dashboard():
    if 'user_id' not in session or session.get('role') != 'professional':
        return redirect(url_for('employee_login'))

    professional_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT
            b.id, u.name AS customer_name, u.phone AS customer_phone,
            b.service_date, b.service_time, b.address,
            s.service_name, s.price, b.status
        FROM bookings b
        JOIN services s ON b.service_id = s.id
        JOIN users u ON b.user_id = u.id
        WHERE b.professional_id = %s
        ORDER BY b.service_date DESC
    """
    cursor.execute(query, (professional_id,))
    jobs = cursor.fetchall()
    conn.close()
    return render_template('employee_dashboard.html', jobs=jobs)

# ========================
# EMPLOYEE: CANCEL JOB
# ========================
@app.route('/employee-cancel/<int:booking_id>', methods=['POST'])
def employee_cancel(booking_id):
    if 'user_id' not in session or session.get('role') != 'professional':
        return redirect(url_for('employee_login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE bookings SET status = 'Cancelled'
        WHERE id = %s AND professional_id = %s
    """, (booking_id, session['user_id']))
    conn.commit()
    conn.close()
    flash('Job marked as cancelled.', 'info')
    return redirect(url_for('employee_dashboard'))

# ========================
# EMPLOYEE: COMPLETE JOB
# ========================
@app.route('/complete-job/<int:booking_id>', methods=['POST'])
def complete_job(booking_id):
    if 'user_id' not in session or session.get('role') != 'professional':
        return redirect(url_for('employee_login'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            UPDATE bookings SET status = 'Completed'
            WHERE id = %s AND professional_id = %s
        """, (booking_id, session['user_id']))
        conn.commit()
        if cursor.rowcount > 0:
            flash('Great job! Task marked as completed.', 'success')
        else:
            flash('Could not update job status. Please try again.', 'error')
    except Exception as e:
        flash('An error occurred while updating the job.', 'error')
    finally:
        conn.close()
    return redirect(url_for('employee_dashboard'))

# ========================
# ADMIN DASHBOARD
# ========================
@app.route('/admin-dashboard')
def admin_dashboard():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT b.id, u.name AS customer_name, b.service_date, b.service_time,
                   b.address, s.service_name, s.price, b.status,
                   b.professional_id, p.name AS professional_name
            FROM bookings b
            JOIN services s ON b.service_id = s.id
            JOIN users u ON b.user_id = u.id
            LEFT JOIN professionals p ON b.professional_id = p.id
            ORDER BY b.id DESC
        """
        cursor.execute(query)
        bookings = cursor.fetchall()

        cursor.execute("SELECT * FROM professionals WHERE status = 'Active'")
        professionals = cursor.fetchall()

        cursor.execute("""
            SELECT COUNT(DISTINCT professional_id) as busy
            FROM bookings
            WHERE status = 'Assigned' AND professional_id IS NOT NULL
        """)
        busy_count = cursor.fetchone()['busy']

        cursor.execute("SELECT COUNT(*) as total FROM professionals")
        total_professionals = cursor.fetchone()['total']

        free_count = total_professionals - busy_count
        total_revenue = sum(
    float(b['price'] or 0) 
    for b in bookings 
    if str(b['status']).strip().capitalize() == 'Completed'
)

    except Exception as e:
        print(f"Dashboard Error: {e}")
        bookings, busy_count, free_count, total_revenue, professionals = [], 0, 0, 0, []

    conn.close()
    return render_template('admin_dashboard.html',
                           bookings=bookings,
                           professionals=professionals,
                           busy_count=busy_count,
                           free_staff=free_count,
                           total_revenue=total_revenue)

# ========================
# ASSIGN JOB
# ========================
@app.route('/assign-job', methods=['POST'])
def assign_job():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('admin_login'))
    booking_id = request.form.get('booking_id')
    professional_id = request.form.get('professional_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE bookings SET professional_id = %s, status = 'Assigned'
        WHERE id = %s
    """, (professional_id, booking_id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

# ========================
# REGISTER
# ========================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name     = request.form.get("name", "").strip()
        email    = request.form.get("email", "").strip().lower()
        phone    = request.form.get("phone", "").strip()
        password = request.form.get("password", "")

        # Input validation
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            flash("Please enter a valid email address.", "error")
            return redirect(url_for("register"))
        if phone and not re.match(r'^[0-9]{10}$', phone):
            flash("Phone number must be exactly 10 digits.", "error")
            return redirect(url_for("register"))
        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return redirect(url_for("register"))

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            conn.close()
            flash("Email already registered!", "error")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        cursor.execute(
            "INSERT INTO users (name, email, phone, password) VALUES (%s, %s, %s, %s)",
            (name, email, phone, hashed_password)
        )
        conn.commit()
        conn.close()
        flash("Registration successful! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

# ========================
# SERVICES PAGE
# ========================
@app.route("/services")
def services_page():
    if "user_id" not in session:
        flash("Please login first!", "error")
        return redirect(url_for("login"))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM services")
    all_services = cursor.fetchall()
    conn.close()
    return render_template("services.html", services=all_services)

# ========================
# ABOUT PAGE
# ========================
@app.route('/about')
def about():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM services")
    services = cursor.fetchall()
    conn.close()
    return render_template('about.html', services=services)

# ========================
# CUSTOMER PROFILE
# ========================
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return "User not found", 404

    query = """
        SELECT b.id, b.service_id, s.service_name, s.price, b.service_date, b.service_time,
               b.status, b.address, b.rating, b.review, b.complaint, b.complaint_status,
               p.name AS professional_name
        FROM bookings b
        JOIN services s ON b.service_id = s.id
        LEFT JOIN professionals p ON b.professional_id = p.id
        WHERE b.user_id = %s
        ORDER BY b.id DESC
    """
    cursor.execute(query, (session['user_id'],))
    bookings = cursor.fetchall()
    conn.close()
    return render_template('profile.html', user=user, bookings=bookings)

# ========================
# USER: CANCEL BOOKING
# ========================
@app.route('/cancel-booking/<int:booking_id>', methods=['POST'])
def cancel_booking(booking_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM bookings WHERE id = %s AND user_id = %s",
                   (booking_id, session['user_id']))
    booking = cursor.fetchone()
    if booking and booking[0] != 'Completed':
        cursor.execute("UPDATE bookings SET status = 'Cancelled' WHERE id = %s", (booking_id,))
        conn.commit()
        flash("Booking cancelled successfully.", "success")
    else:
        flash("Cannot cancel this booking.", "error")
    conn.close()
    return redirect(url_for('profile'))

# ========================
# RAZORPAY CONFIGURATION
# ========================
RAZORPAY_KEY_ID     = os.getenv("RAZORPAY_KEY_ID", "rzp_test_XXXXXXXXXXXXXXXX")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "XXXXXXXXXXXXXXXXXXXXXXXX")

def get_razorpay_client():
    if razorpay is None:
        raise RuntimeError("razorpay package not installed. Run: pip install razorpay")
    return razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# ========================
# INITIATE RAZORPAY PAYMENT
# ========================
@app.route("/initiate-payment/<service_ids>")
def initiate_payment(service_ids):
    if "user_id" not in session:
        return redirect(url_for("login"))

    id_list = [int(i) for i in service_ids.split(",") if i.strip()]
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    format_strings = ','.join(['%s'] * len(id_list))
    cursor.execute(f"SELECT id, service_name, price FROM services WHERE id IN ({format_strings})", tuple(id_list))
    selected_services = cursor.fetchall()
    conn.close()

    total_amount = sum(s['price'] for s in selected_services)
    amount_paise = int(total_amount * 100)  # Razorpay needs paise

    try:
        client = get_razorpay_client()
        order = client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "receipt": f"fixbuddy_{session['user_id']}_{secrets.token_hex(4)}",
            "notes": {
                "service_ids": service_ids,
                "user_id": str(session['user_id'])
            }
        })
        razorpay_order_id = order['id']
    except Exception as e:
        print(f"[Razorpay] Order creation failed: {e}")
        flash("Payment gateway error. Please try again.", "error")
        return redirect(url_for("services_page"))

    return render_template(
        "razorpay_checkout.html",
        total=total_amount,
        services=selected_services,
        service_ids=service_ids,
        razorpay_key=RAZORPAY_KEY_ID,
        razorpay_order_id=razorpay_order_id,
        user_name=session.get('user_name', ''),
        amount_paise=amount_paise
    )

# ========================
# RAZORPAY PAYMENT SUCCESS
# ========================
@app.route("/razorpay-success", methods=["POST"])
@csrf.exempt  # Razorpay posts back without a CSRF token
def razorpay_success():
    if "user_id" not in session:
        return redirect(url_for("login"))

    razorpay_payment_id = request.form.get("razorpay_payment_id", "")
    razorpay_order_id   = request.form.get("razorpay_order_id", "")
    razorpay_signature  = request.form.get("razorpay_signature", "")
    service_ids         = request.form.get("service_ids", "")

    print(f"[Razorpay] payment_id={razorpay_payment_id}")
    print(f"[Razorpay] order_id={razorpay_order_id}")
    print(f"[Razorpay] signature={razorpay_signature}")
    print(f"[Razorpay] service_ids={service_ids}")
    print(f"[Razorpay] KEY_SECRET used={RAZORPAY_KEY_SECRET[:6]}...")

    # Verify HMAC-SHA256 signature
    try:
        body = razorpay_order_id + "|" + razorpay_payment_id
        mac = hmac.new(
            RAZORPAY_KEY_SECRET.encode(),
            body.encode(),
            hashlib.sha256
        )
        expected_sig = mac.hexdigest()
        print(f"[Razorpay] expected={expected_sig}")
        print(f"[Razorpay] received={razorpay_signature}")
        if not hmac.compare_digest(expected_sig, razorpay_signature):
            print("[Razorpay] SIGNATURE MISMATCH")
            flash("Payment verification failed. Contact support.", "error")
            return redirect(url_for("services_page"))
        print("[Razorpay] Signature OK")
    except Exception as e:
        print(f"[Razorpay] Signature error: {e}")
        flash("Payment verification error.", "error")
        return redirect(url_for("services_page"))

    # Create bookings after successful payment
    try:
        id_list = [int(i) for i in service_ids.split(",") if i.strip()]
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        format_strings = ','.join(['%s'] * len(id_list))
        cursor.execute(f"SELECT * FROM services WHERE id IN ({format_strings})", tuple(id_list))
        selected_services = cursor.fetchall()
        print(f"[Razorpay] Services found: {[s['id'] for s in selected_services]}")

        new_booking_ids = []
        for service in selected_services:
            cursor.execute(
                "INSERT INTO bookings (user_id, service_id, booking_date, status) VALUES (%s, %s, CURDATE(), 'Paid')",
                (session["user_id"], service['id'])
            )
            new_id = cursor.lastrowid
            new_booking_ids.append(str(new_id))
            cursor.execute(
                "INSERT INTO payments (booking_id, payment_method, payment_status, transaction_id) "
                "VALUES (%s, %s, %s, %s)",
                (new_id, "Razorpay", "Paid", razorpay_payment_id)
            )
            print(f"[Razorpay] Created booking {new_id} for service {service['id']}")

        conn.commit()
        conn.close()
        ids_param = ",".join(new_booking_ids)
        print(f"[Razorpay] Redirecting to booking_details with ids={ids_param}")
        return redirect(url_for("booking_details", transaction_ids=ids_param))
    except Exception as e:
        print(f"[Razorpay] Booking creation error: {e}")
        flash(f"Payment received but booking failed: {e}. Please contact support with payment ID: {razorpay_payment_id}", "error")
        return redirect(url_for("services_page"))


# ========================
# RAZORPAY PAYMENT FAILURE
# ========================
@app.route("/razorpay-failure", methods=["POST"])
@csrf.exempt  # Razorpay posts back without a CSRF token
def razorpay_failure():
    error_desc = request.form.get("error_description", "Payment was not completed.")
    service_ids = request.form.get("service_ids", "")
    flash(f"Payment failed: {error_desc}", "error")
    if service_ids:
        return redirect(url_for("initiate_payment", service_ids=service_ids))
    return redirect(url_for("services_page"))

# ========================
# OLD PAYMENT PAGE (backward compat — redirects to Razorpay)
# ========================
@app.route("/payment/<service_ids>", methods=["GET", "POST"])
def payment_page(service_ids):
    if "user_id" not in session:
        flash("Please login first!", "error")
        return redirect(url_for("login"))
    return redirect(url_for("initiate_payment", service_ids=service_ids))

# ========================
# BOOKING DETAILS (Assign Any Worker)
# ========================
@app.route("/booking-details/<transaction_ids>", methods=["GET", "POST"])
def booking_details(transaction_ids):
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        house_no = request.form.get("house_no")
        society = request.form.get("society")
        street = request.form.get("street")
        area = request.form.get("area")
        customer_email = request.form.get("customer_email")
        full_address = f"{house_no}, {society}, {street}, {area}"

        selected_date = request.form.get("service_date")
        if request.form.get("date_type") == "today":
            selected_date = date.today().strftime('%Y-%m-%d')
        selected_time = request.form.get("service_time")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        id_list = [int(i) for i in transaction_ids.split(",") if i.strip()]
        format_strings = ','.join(['%s'] * len(id_list))

        query = f"UPDATE bookings SET address=%s, service_date=%s, service_time=%s, status='Pending' WHERE id IN ({format_strings})"
        cursor.execute(query, (full_address, selected_date, selected_time) + tuple(id_list))

        # Auto-assignment
        for b_id in id_list:
            cursor.execute("SELECT s.service_name FROM services s JOIN bookings b ON b.service_id = s.id WHERE b.id = %s", (b_id,))
            result = cursor.fetchone()
            if result:
                service_name = result['service_name'].lower()
                required_type = None
                if "clean" in service_name:   required_type = "Cleaner"
                elif "plumb" in service_name or "pipe" in service_name: required_type = "Plumber"
                elif "electric" in service_name or "light" in service_name: required_type = "Electrician"
                elif "carpenter" in service_name or "wood" in service_name: required_type = "Carpenter"
                elif "paint" in service_name: required_type = "Painter"
                elif any(k in service_name for k in ("wax","facial","salon","hair","beauty")): required_type = "Beautician"

                if required_type:
                    cursor.execute("""
                        SELECT id, name FROM professionals
                        WHERE service_type = %s AND status = 'Active'
                        AND id NOT IN (
                            SELECT professional_id FROM bookings
                            WHERE service_date = %s AND service_time = %s
                            AND status = 'Assigned' AND professional_id IS NOT NULL
                        )
                        LIMIT 1
                    """, (required_type, selected_date, selected_time))
                    worker = cursor.fetchone()
                    if worker:
                        cursor.execute("UPDATE bookings SET professional_id=%s, status='Assigned' WHERE id=%s",
                                       (worker['id'], b_id))

        email_query = f"SELECT s.service_name, s.price FROM bookings b JOIN services s ON b.service_id = s.id WHERE b.id IN ({format_strings})"
        cursor.execute(email_query, tuple(id_list))
        selected_services = cursor.fetchall()
        total_price = sum(s['price'] for s in selected_services) if selected_services else 0

        conn.commit()
        conn.close()

        if customer_email:
            send_booking_email_async(
                customer_email, selected_services, total_price,
                full_address, selected_date, selected_time
            )

        return redirect(url_for('success', booking_ids=transaction_ids))

    return render_template("booking_details.html", booking_ids=transaction_ids)

# ========================
# SUCCESS PAGE
# ========================
@app.route('/success/<booking_ids>')
def success(booking_ids):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    ids_list = booking_ids.split(',')
    format_strings = ','.join(['%s'] * len(ids_list))
    query = f"""
        SELECT b.id, s.service_name, s.price, b.service_date, b.service_time,
               p.name AS professional_name
        FROM bookings b
        JOIN services s ON b.service_id = s.id
        LEFT JOIN professionals p ON b.professional_id = p.id
        WHERE b.id IN ({format_strings})
    """
    cursor.execute(query, tuple(ids_list))
    bookings = cursor.fetchall()
    conn.close()
    total_price = sum(item['price'] for item in bookings)
    return render_template('success.html', bookings=bookings, total=total_price)

# ========================
# USER: SUBMIT RATING
# ========================
@app.route('/submit-rating', methods=['POST'])
def submit_rating():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    booking_id = request.form.get('booking_id')
    rating = request.form.get('rating')
    review = request.form.get('review', '').strip()
    # Validate rating is an integer 1-5
    try:
        rating_int = int(rating)
        if not (1 <= rating_int <= 5):
            raise ValueError
    except (TypeError, ValueError):
        flash("Invalid rating value.", "error")
        return redirect(url_for('profile'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE bookings SET rating = %s, review = %s
        WHERE id = %s AND user_id = %s
    """, (rating_int, review, booking_id, session['user_id']))
    conn.commit()
    conn.close()
    flash("Thank you for your feedback!", "success")
    return redirect(url_for('profile'))

# ========================
# USER: SUBMIT COMPLAINT
# ========================
@app.route('/submit-complaint', methods=['POST'])
def submit_complaint():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    booking_id = request.form.get('booking_id')
    complaint_text = request.form.get('complaint')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE bookings SET complaint = %s, complaint_status = 'Pending'
        WHERE id = %s AND user_id = %s
    """, (complaint_text, booking_id, session['user_id']))
    conn.commit()
    conn.close()
    flash("Your complaint has been registered. Support will contact you shortly.", "warning")
    return redirect(url_for('profile'))

# ========================
# ADMIN PROFESSIONALS
# ========================
@app.route('/admin-professionals')
def admin_professionals():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('admin_login'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM professionals ORDER BY id DESC")
    professionals = cursor.fetchall()
    cursor.execute("SELECT DISTINCT professional_id FROM bookings WHERE status = 'Assigned' AND professional_id IS NOT NULL")
    busy_worker_ids = [row['professional_id'] for row in cursor.fetchall()]
    conn.close()
    return render_template('admin_professionals.html', professionals=professionals, busy_worker_ids=busy_worker_ids)

@app.route('/toggle-status/<int:id>', methods=['POST'])
def toggle_status(id):
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('admin_login'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT status FROM professionals WHERE id = %s", (id,))
    prof = cursor.fetchone()
    if prof:
        new_status = 'Inactive' if prof['status'] == 'Active' else 'Active'
        cursor.execute("UPDATE professionals SET status = %s WHERE id = %s", (new_status, id))
        conn.commit()
    conn.close()
    return redirect(url_for('admin_professionals'))

# ========================
# ADMIN: VIEW COMPLAINTS
# ========================
@app.route('/admin-complaints')
def admin_complaints():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('admin_login'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT b.id, u.name AS customer_name, u.email AS customer_email,
               s.service_name, b.complaint, b.complaint_status,
               b.service_date, p.name AS professional_name
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        JOIN services s ON b.service_id = s.id
        LEFT JOIN professionals p ON b.professional_id = p.id
        WHERE b.complaint IS NOT NULL AND b.complaint != ''
        ORDER BY b.id DESC
    """)
    complaints = cursor.fetchall()
    conn.close()
    return render_template('admin_complaints.html', complaints=complaints)

@app.route('/resolve-complaint/<int:booking_id>', methods=['POST'])
def resolve_complaint(booking_id):
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('admin_login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE bookings SET complaint_status='Resolved' WHERE id=%s", (booking_id,))
    conn.commit()
    conn.close()
    flash('Complaint marked as resolved.', 'success')
    return redirect(url_for('admin_complaints'))

# ========================
# CANCEL PAGE
# ========================
@app.route("/cancel/<int:booking_id>")
def cancel_page(booking_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE bookings SET status='Cancelled' WHERE id = %s AND user_id = %s",
                   (booking_id, session["user_id"]))
    conn.commit()
    conn.close()
    flash("Booking cancelled successfully.", "success")
    return redirect(url_for("services_page"))

# ========================
# ADMIN: EXPORT CSV
# ========================
@app.route('/admin-export-csv')
def admin_export_csv():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('admin_login'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT b.id, u.name AS customer, u.email AS customer_email,
               s.service_name, s.price, b.service_date, b.service_time,
               b.address, b.status, p.name AS professional,
               b.rating, b.complaint, b.complaint_status
        FROM bookings b
        JOIN services s ON b.service_id = s.id
        JOIN users u ON b.user_id = u.id
        LEFT JOIN professionals p ON b.professional_id = p.id
        ORDER BY b.id DESC
    """)
    bookings = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        'id', 'customer', 'customer_email', 'service_name', 'price',
        'service_date', 'service_time', 'address', 'status',
        'professional', 'rating', 'complaint', 'complaint_status'
    ])
    writer.writeheader()
    for row in bookings:
        writer.writerow(row)

    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=fix_buddy_bookings.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response

# ========================
# CUSTOMER: EDIT PROFILE
# ========================
@app.route('/edit-profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
    user = cursor.fetchone()

    if request.method == 'POST':
        new_name  = request.form.get('name', '').strip()
        new_phone = request.form.get('phone', '').strip()
        new_pass  = request.form.get('new_password', '').strip()
        cur_pass  = request.form.get('current_password', '').strip()

        # Validate phone
        if new_phone and not re.match(r'^[0-9]{10}$', new_phone):
            flash('Phone number must be exactly 10 digits.', 'error')
            conn.close()
            return redirect(url_for('edit_profile'))

        if not check_password_hash(user['password'], cur_pass):
            flash('Current password is incorrect.', 'error')
            conn.close()
            return redirect(url_for('edit_profile'))

        if new_pass:
            hashed = generate_password_hash(new_pass, method='pbkdf2:sha256')
            cursor.execute(
                "UPDATE users SET name=%s, phone=%s, password=%s WHERE id=%s",
                (new_name, new_phone, hashed, session['user_id'])
            )
        else:
            cursor.execute(
                "UPDATE users SET name=%s, phone=%s WHERE id=%s",
                (new_name, new_phone, session['user_id'])
            )
        conn.commit()
        conn.close()
        session['user_name'] = new_name
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))

    conn.close()
    return render_template('edit_profile.html', user=user)

# ========================
# LOGOUT
# ========================
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("login"))

# ========================
# FORGOT PASSWORD
# ========================
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user:
            token = secrets.token_urlsafe(32)
            expires = datetime.now() + timedelta(hours=1)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS password_resets (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    token VARCHAR(100) NOT NULL UNIQUE,
                    expires_at DATETIME NOT NULL,
                    used TINYINT(1) DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            cursor.execute(
                "INSERT INTO password_resets (user_id, token, expires_at) VALUES (%s, %s, %s)",
                (user['id'], token, expires)
            )
            conn.commit()
            reset_link = url_for('reset_password', token=token, _external=True)
            send_reset_email_async(email, user['name'], reset_link)

        conn.close()
        flash("If your email is registered, you'll receive a reset link shortly.", "success")
        return redirect(url_for('forgot_password'))

    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT pr.*, u.email FROM password_resets pr
        JOIN users u ON pr.user_id = u.id
        WHERE pr.token = %s AND pr.used = 0 AND pr.expires_at > NOW()
    """, (token,))
    reset = cursor.fetchone()

    if not reset:
        conn.close()
        flash("This reset link is invalid or has expired.", "error")
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_pass     = request.form.get('password', '').strip()
        confirm_pass = request.form.get('confirm_password', '').strip()

        if not new_pass or len(new_pass) < 6:
            flash("Password must be at least 6 characters.", "error")
            conn.close()
            return redirect(request.url)

        if new_pass != confirm_pass:
            flash("Passwords do not match.", "error")
            conn.close()
            return redirect(request.url)

        hashed = generate_password_hash(new_pass, method='pbkdf2:sha256')
        cursor.execute("UPDATE users SET password=%s WHERE id=%s", (hashed, reset['user_id']))
        cursor.execute("UPDATE password_resets SET used=1 WHERE token=%s", (token,))
        conn.commit()
        conn.close()
        flash("Password reset successfully! Please log in.", "success")
        return redirect(url_for('login'))

    conn.close()
    return render_template('reset_password.html', token=token, email=reset['email'])

# ========================
# CUSTOMER: RE-BOOK
# ========================
@app.route('/rebook/<int:service_id>')
def rebook(service_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('initiate_payment', service_ids=str(service_id)))

# ========================
# GLOBAL ERROR HANDLERS
# ========================
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500


if __name__ == "__main__":
    app.run(debug=True)
