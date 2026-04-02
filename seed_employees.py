"""
Fix Buddy — Seed 9 professional employees into the database.
Password for all: Pass@1234
Run: python seed_employees.py
"""
import mysql.connector
from werkzeug.security import generate_password_hash
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", ""),
    database=os.getenv("DB_NAME", "fix_buddy")
)
cursor = conn.cursor()

DEFAULT_PASSWORD = "Pass@1234"
hashed = generate_password_hash(DEFAULT_PASSWORD, method='pbkdf2:sha256')

employees = [
    # (name, email, phone, service_type, experience)
    ("Rajan Sharma",  "rajan.sharma@fixbuddy.com",  "9876543201", "Electrician", 5),
    ("Suresh Patil",  "suresh.patil@fixbuddy.com",  "9876543202", "Plumber",     7),
    ("Anjali Verma",  "anjali.verma@fixbuddy.com",  "9876543203", "Cleaner",     3),
    ("Deepak Mehta",  "deepak.mehta@fixbuddy.com",  "9876543204", "Carpenter",   6),
    ("Mohan Das",     "mohan.das@fixbuddy.com",     "9876543205", "Painter",     4),
    ("Priya Nair",    "priya.nair@fixbuddy.com",    "9876543206", "Beautician",  5),
    ("Kavita Singh",  "kavita.singh@fixbuddy.com",  "9876543207", "Cleaner",     2),
    ("Arjun Kumar",   "arjun.kumar@fixbuddy.com",   "9876543208", "Electrician", 3),
    ("Sneha Joshi",   "sneha.joshi@fixbuddy.com",   "9876543209", "Beautician",  4),
]

inserted = 0
skipped  = 0

for name, email, phone, stype, exp in employees:
    # Skip if email already exists
    cursor.execute("SELECT id FROM professionals WHERE email = %s", (email,))
    if cursor.fetchone():
        print(f"  SKIP (already exists): {name} <{email}>")
        skipped += 1
        continue

    cursor.execute("""
        INSERT INTO professionals (name, email, phone, service_type, experience, password, status)
        VALUES (%s, %s, %s, %s, %s, %s, 'Active')
    """, (name, email, phone, stype, exp, hashed))
    print(f"  [OK] Inserted: {name} ({stype})")
    inserted += 1

conn.commit()
conn.close()

print(f"\nDone — {inserted} inserted, {skipped} skipped.")
print(f"Login password for all employees: {DEFAULT_PASSWORD}")
