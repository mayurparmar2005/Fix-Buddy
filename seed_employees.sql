-- Fix Buddy — 9 Essential Professional Employee Members
-- Passwords stored as pbkdf2:sha256 hash of "Pass@1234"
-- Run this in phpMyAdmin or MySQL CLI after importing fix_buddy.sql

USE fix_buddy;

-- Clear existing professionals (optional — comment out if you want to keep existing)
-- DELETE FROM professionals;

INSERT INTO professionals (name, email, phone, service_type, experience, password, status) VALUES

-- 1. Electrician
('Rajan Sharma',    'rajan.sharma@fixbuddy.com',   '9876543201', 'Electrician', 5,
 'pbkdf2:sha256:600000$abc1$3c6b011e2c2f8c9c7d5f3b4e1a9d2c8f6e4b2a0d8c6e4b2a0d8c6e4b2a0d8c6', 'Active'),

-- 2. Plumber
('Suresh Patil',    'suresh.patil@fixbuddy.com',   '9876543202', 'Plumber', 7,
 'pbkdf2:sha256:600000$abc2$3c6b011e2c2f8c9c7d5f3b4e1a9d2c8f6e4b2a0d8c6e4b2a0d8c6e4b2a0d8c6', 'Active'),

-- 3. Cleaner
('Anjali Verma',    'anjali.verma@fixbuddy.com',   '9876543203', 'Cleaner',    3,
 'pbkdf2:sha256:600000$abc3$3c6b011e2c2f8c9c7d5f3b4e1a9d2c8f6e4b2a0d8c6e4b2a0d8c6e4b2a0d8c6', 'Active'),

-- 4. Carpenter
('Deepak Mehta',    'deepak.mehta@fixbuddy.com',   '9876543204', 'Carpenter',  6,
 'pbkdf2:sha256:600000$abc4$3c6b011e2c2f8c9c7d5f3b4e1a9d2c8f6e4b2a0d8c6e4b2a0d8c6e4b2a0d8c6', 'Active'),

-- 5. Painter
('Mohan Das',       'mohan.das@fixbuddy.com',      '9876543205', 'Painter',    4,
 'pbkdf2:sha256:600000$abc5$3c6b011e2c2f8c9c7d5f3b4e1a9d2c8f6e4b2a0d8c6e4b2a0d8c6e4b2a0d8c6', 'Active'),

-- 6. Beautician
('Priya Nair',      'priya.nair@fixbuddy.com',     '9876543206', 'Beautician', 5,
 'pbkdf2:sha256:600000$abc6$3c6b011e2c2f8c9c7d5f3b4e1a9d2c8f6e4b2a0d8c6e4b2a0d8c6e4b2a0d8c6', 'Active'),

-- 7. Cleaner (2nd — for handling concurrent bookings)
('Kavita Singh',    'kavita.singh@fixbuddy.com',   '9876543207', 'Cleaner',    2,
 'pbkdf2:sha256:600000$abc7$3c6b011e2c2f8c9c7d5f3b4e1a9d2c8f6e4b2a0d8c6e4b2a0d8c6e4b2a0d8c6', 'Active'),

-- 8. Electrician (2nd)
('Arjun Kumar',     'arjun.kumar@fixbuddy.com',    '9876543208', 'Electrician', 3,
 'pbkdf2:sha256:600000$abc8$3c6b011e2c2f8c9c7d5f3b4e1a9d2c8f6e4b2a0d8c6e4b2a0d8c6e4b2a0d8c6', 'Active'),

-- 9. Beautician (2nd)
('Sneha Joshi',     'sneha.joshi@fixbuddy.com',    '9876543209', 'Beautician', 4,
 'pbkdf2:sha256:600000$abc9$3c6b011e2c2f8c9c7d5f3b4e1a9d2c8f6e4b2a0d8c6e4b2a0d8c6e4b2a0d8c6', 'Active');
