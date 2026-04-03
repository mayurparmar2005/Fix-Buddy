Fix Buddy — Home Services Application
======================================

A Flask + MySQL web application for booking home services (cleaning, 
plumbing, electrician, beauty/salon, etc.) with customer, employee, 
and admin portals.

This project is hosted on pythonanywhere.com you can visit our side: https://fixbuddy04.pythonanywhere.com/
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TECH STACK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Backend  : Python 3 / Flask
  Database : MySQL (via XAMPP / mysql-connector-python)
  Email    : Flask-Mail → Gmail SMTP
  Frontend : Vanilla HTML + CSS + JS (Font Awesome, SweetAlert2)
  Security : werkzeug password hashing (pbkdf2:sha256)
  Config   : python-dotenv (.env file)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QUICK START
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Start XAMPP → Apache + MySQL

2. Create the database in phpMyAdmin:
     CREATE DATABASE fix_buddy;
   Then import fix_buddy.sql if available.
   Then import seed_employees.sql if available.

3. Copy environment file:
     Copy .env and edit credentials if needed:
       SECRET_KEY   = any long random string
       DB_PASSWORD  = your MySQL root password (blank for XAMPP default)
       MAIL_PASSWORD = your Gmail app password

4. Install dependencies:
     pip install flask flask-mail mysql-connector-python werkzeug
                 python-dotenv qrcode pillow sweetalert2

5. Run the app:
     python app.py
   Then open: http://127.0.0.1:5000

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PORTALS & ROUTES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CUSTOMER
  /                 Customer login
  /register         Customer sign-up (name, email, phone, password)
  /forgot-password  Request password reset email
  /reset-password/  Set new password via token link
  /services         Browse & search services, add to cart
  /profile          View bookings, rate, re-book, file complaint
  /edit-profile     Update name, phone, password
  /success          Post-payment receipt page

ADMIN (login: /admin-login)
  /admin-dashboard  Revenue, bookings, staff stats overview
  /admin-professionals  Manage professionals (activate/deactivate)
  /admin-complaints  View & resolve customer complaints
  /admin-export-csv  Download all bookings as fix_buddy_bookings.csv

EMPLOYEE (login: /employee-login)
  /employee-dashboard  View assigned bookings, update status

OTHER
  /about            About page
  /logout           Clear session and redirect to login

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
KEY FEATURES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✔ Cart with add/remove, expandable item list, real-time total
✔ Dynamic UPI QR code payment (qrcode lib)
✔ Professional auto-assignment after booking
✔ Email receipt on booking confirmation (Flask-Mail)
✔ Password reset via email token (1-hour expiry)
✔ Employee passwords hashed with pbkdf2:sha256
✔ Customer: edit profile, re-book, rate service, file complaints
✔ Admin: CSV export, complaints management, staff control
✔ Mobile-responsive navbar with hamburger menu
✔ Loading spinner on booking form submission
✔ Flash message auto-dismiss (4-second fade)
✔ Session idle timeout warning (SweetAlert2, 20-minute logout)
✔ Custom 404 and 500 error pages
✔ Lazy-loaded service images

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEFAULT ADMIN CREDENTIALS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Username : admin
  Password : admin123
  ⚠ Change these in app.py before production!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ENVIRONMENT (.env)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  SECRET_KEY       Flask session secret key
  DB_HOST          Database host (default: localhost)
  DB_USER          Database user (default: root)
  DB_PASSWORD      Database password (default: blank)
  DB_NAME          Database name (default: fix_buddy)
  MAIL_USERNAME    Gmail address for outgoing emails
  MAIL_PASSWORD    Gmail app password (16-char)
  MAIL_DEFAULT_SENDER  Sender display address

IMPORTANT: .env is listed in .gitignore and must NEVER be committed.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DATABASE TABLES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  users             Customer accounts
  professionals     Employee accounts
  services          Service catalog
  bookings          All booking records
  password_resets   Token-based reset requests (auto-created)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PROJECT STRUCTURE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  app.py               Main Flask application
  .env                 Environment variables (secrets)
  .gitignore           Files excluded from version control
  templates/           All Jinja2 HTML templates
    index.html         Customer login
    register.html      Customer sign-up
    forgot_password.html  Forgot password request
    reset_password.html   New password form
    services.html      Main services + cart page
    profile.html       Customer bookings + actions
    edit_profile.html  Edit name, phone, password
    booking_details.html  Address + schedule form
    fake_qr.html       UPI QR payment page
    success.html       Post-payment receipt
    admin_dashboard.html  Admin overview
    admin_professionals.html  Staff management
    admin_complaints.html  Complaints management
    employee_dashboard.html  Employee view
    404.html / 500.html   Custom error pages
  static/
    css/style.css      Global stylesheet
    images/            Logo and service images
