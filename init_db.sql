-- Create the database
CREATE DATABASE IF NOT EXISTS customer_service;
USE customer_service;

-- ==========================================
-- 1. CREATE TABLES [cite: 81-114]
-- ==========================================

-- Customers Table [cite: 82-88]
CREATE TABLE IF NOT EXISTS customers (
    customer_id INT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders Table [cite: 89-97]
CREATE TABLE IF NOT EXISTS orders (
    order_id INT PRIMARY KEY,
    customer_id INT,
    product_name TEXT,
    status VARCHAR(50),
    order_date TIMESTAMP,
    delivery_date TIMESTAMP
);

-- Complaints Table [cite: 98-106]
CREATE TABLE IF NOT EXISTS complaints (
    complaint_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    order_id INT,
    issue TEXT,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Customer Memory Table (Long-Term Memory) [cite: 107-114]
-- Note: 'key' is a reserved word in MySQL, so it is wrapped in backticks (`key`)
CREATE TABLE IF NOT EXISTS customer_memory (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    `key` TEXT,
    value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- 2. INSERT MOCK DATA
-- ==========================================

-- Insert Mock Customers
INSERT INTO customers (customer_id, name, email) VALUES
(1, 'Alice Smith', 'alice@example.com'),
(2, 'Bob Johnson', 'bob@example.com'),
(3, 'Charlie Davis', 'charlie@example.com');

-- Insert Mock Orders (Aligned with Test Cases) [cite: 164]
-- Order 12345: For intent parsing test
-- Order 1001: For OrderLookup tool test
-- Order 5678: For Refund tool test
-- Order 2222: For Complaint logger test
-- Order 7890: For multi-step reasoning (refund if delivered)
INSERT INTO orders (order_id, customer_id, product_name, status, order_date, delivery_date) VALUES
(12345, 1, 'Wireless Mouse', 'shipped', '2023-10-01 10:00:00', NULL),
(1001, 2, 'Mechanical Keyboard', 'processing', '2023-10-25 14:30:00', NULL),
(5678, 1, 'Noise Cancelling Headphones', 'delivered', '2023-09-15 09:00:00', '2023-09-18 12:00:00'),
(2222, 3, 'Ergonomic Chair', 'delivered', '2023-08-20 11:15:00', '2023-08-25 16:45:00'),
(7890, 2, 'USB-C Hub', 'delivered', '2023-10-20 08:20:00', '2023-10-22 10:10:00');

-- Insert Mock Complaints
INSERT INTO complaints (customer_id, order_id, issue, status) VALUES
(3, 2222, 'The chair arrived with a scratched leg.', 'open');

-- Insert Mock Long-Term Memory [cite: 123-127, 164]
-- Setting up the "Remember I prefer refunds" test case
INSERT INTO customer_memory (customer_id, `key`, value) VALUES
(1, 'resolution_preference', 'prefers refunds over store credit'),
(3, 'past_issues', 'frequent late deliveries');