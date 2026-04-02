-- 1. DROP EXISTING TABLES (Clean Slate)
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS bookings;
DROP TABLE IF EXISTS services;
DROP TABLE IF EXISTS professionals;
DROP TABLE IF EXISTS users;

-- 2. CREATE USERS TABLE
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    role ENUM('customer', 'admin') DEFAULT 'customer',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. CREATE PROFESSIONALS TABLE
CREATE TABLE professionals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    service_type VARCHAR(255) NOT NULL, -- Stores categories like "Cleaning,Plumbing"
    experience INT NOT NULL,
    status ENUM('Active', 'Inactive') DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. CREATE SERVICES TABLE
CREATE TABLE services (
    id INT AUTO_INCREMENT PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    category VARCHAR(50) NOT NULL,
    target_gender VARCHAR(20) DEFAULT 'all', -- Added this column from your SS
    image_url VARCHAR(255)
);

-- 5. CREATE BOOKINGS TABLE (The Fixed Version)
CREATE TABLE bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    service_id INT NOT NULL,
    professional_id INT DEFAULT NULL,
    booking_date DATE DEFAULT NULL,
    service_date DATE DEFAULT NULL,
    service_time VARCHAR(20) DEFAULT NULL,
    address TEXT DEFAULT NULL,
    status VARCHAR(50) DEFAULT 'Pending',
    rating INT DEFAULT NULL,
    review TEXT DEFAULT NULL,
    complaint TEXT DEFAULT NULL,
    complaint_status VARCHAR(50) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE CASCADE,
    FOREIGN KEY (professional_id) REFERENCES professionals(id) ON DELETE SET NULL
);

-- 6. CREATE PAYMENTS TABLE
CREATE TABLE payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    payment_status VARCHAR(50) DEFAULT 'Pending',
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE
);

-- SERVICES ADDDING
INSERT INTO services (id, service_name, description, price, category, target_gender) VALUES
(1, 'Carpentry', NULL, 400.00, 'New', 'all'),
(2, 'Electrical Repair', NULL, 450.00, 'New', 'all'),
(3, 'Painting', NULL, 350.00, 'New', 'all'),
(4, 'Laundry Service', NULL, 250.00, 'New', 'all'),
(5, 'Gardening', NULL, 300.00, 'New', 'all'),
(6, 'Roof Repair', NULL, 600.00, 'New', 'all'),
(7, 'Smart Home Setup', 'Installation of smart bulbs and Alexa.', 1500.00, 'New', 'all'),
(8, 'Pet Care', 'Protection against cockroaches and ants.', 450.00, 'New', 'all'),
(9, 'Bathroom Deep Cleaning', 'Scrubbing of tiles and fixtures.', 499.00, 'Cleaning', 'all'),
(10, 'Sofa Cleaning', 'Professional shampooing.', 599.00, 'Cleaning', 'all'),
(11, 'Full Home Cleaning', 'Deep cleaning of all rooms.', 2499.00, 'Cleaning', 'all'),
(12, 'Kitchen Cleaning', 'Degreasing of chimneys.', 899.00, 'Cleaning', 'all'),
(13, 'Carpet Shampooing', 'Removal of stains/odors.', 399.00, 'Cleaning', 'all'),
(14, 'Water Tank Cleaning', 'Scrubbing and UV treatment.', 799.00, 'Cleaning', 'all'),
(15, 'Window Cleaning', 'Glass polishing and dust removal.', 299.00, 'Cleaning', 'all'),
(16, 'Balcony Cleaning', 'Floor scrubbing.', 199.00, 'Cleaning', 'all'),
(17, 'Chocolate Waxing (Full Arms)', 'Smooth hair removal for sensitive skin.', 399.00, 'Women Salon', 'female'),
(18, 'Deep Cleanse Facial', 'Revitalizing skin treatment for natural glow.', 899.00, 'Women Salon', 'female'),
(19, 'Pedicure & Manicure Spa', 'Relaxing treatment for hands and feet.', 699.00, 'Women Salon', 'female'),
(20, 'Hair Coloring (L\'Oreal)', 'Professional application for vibrant color.', 1299.00, 'Women Salon', 'female'),
(21, 'Threading (Eyebrows & Lip)', 'Precision shaping by experts.', 99.00, 'Women Salon', 'female'),
(22, 'Head Massage (30 Mins)', 'Relaxing oil massage to relieve stress.', 299.00, 'Women Salon', 'female'),
(23, 'Hair Spa & Nourishment', 'Deep conditioning for frizzy hair.', 799.00, 'Women Salon', 'female'),
(24, 'Bridal Makeup Trial', 'Consultation and sample makeup look.', 1500.00, 'Women Salon', 'female');