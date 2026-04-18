# 🛠️ Fix Buddy — Home Services Marketplace

FixBuddy is a robust, full-stack web application designed to connect homeowners with skilled service professionals like cleaners, plumbers, and electricians. Built using the **Flask** framework and a MySQL backend, it features a complete service lifecycle—from discovery to secure payment and automated assignment.



---

## 🚀 Live Demo & Video:
Live Website: https://fixbuddy04.pythonanywhere.com
Demo Video: https://drive.google.com/file/d/1vJNwtp5o4efqM9kt1CP1GtwhKShGL9FM/view?usp=share_link

---

## 💻 Tech Stack
Backend: Python 3 / Flask
Database: MySQL (via XAMPP / mysql-connector-python)
Security: Werkzeug Password Hashing (pbkdf2:sha256)
Email: Flask-Mail (Gmail SMTP Integration)
Frontend: Vanilla HTML5, CSS3 (Premium Glassmorphism), JavaScript
Libraries: `qrcode`, `pillow`, `python-dotenv`, `sweetalert2`

---

## ✨ Key Features
Advanced Cart: Real-time total calculation with a responsive, expandable item list.
UPI Payments: Dynamic QR code generation for secure, frictionless payments.
Smart Assignment: Automatic professional assignment immediately after booking confirmation.
Automated Alerts: Instant email receipts sent via Flask-Mail upon booking.
Security First: 1-hour expiry tokens for password resets and 20-minute idle session timeouts.
Admin Power: Export booking records to CSV and manage professionals or customer complaints from a central dashboard.

---

## 🛠️ Installation & Setup

1. Database Setup:
   * Start XAMPP (Apache + MySQL).
   * Create a database: `CREATE DATABASE fix_buddy;`.
   * Import `fix_buddy.sql` and `seed_employees.sql`.

2. Environment Configuration:
   * Create a `.env` file in the root directory:
     ```env
     SECRET_KEY=your_random_secret_key
     DB_PASSWORD=your_mysql_password
     MAIL_PASSWORD=your_gmail_app_password
     MAIL_USERNAME=your_email@gmail.com
     ```

3. Install Dependencies:
   ```bash
   pip install flask flask-mail mysql-connector-python werkzeug python-dotenv qrcode pillow
