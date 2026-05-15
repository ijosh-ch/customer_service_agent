-- ============================================================
-- init_db.sql — Schema + seed data for Customer Service Agent
-- Target: MySQL @ 140.118.122.119 / llm-course
-- Run: mysql -h 140.118.122.119 -u llm-student -pllm12345 llm-course < init_db.sql
-- ============================================================

-- ==========================================
-- 1. TABLES
-- ==========================================

CREATE TABLE IF NOT EXISTS customers (
    customer_id INT PRIMARY KEY,
    name        VARCHAR(100),
    email       VARCHAR(100),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    order_id      INT PRIMARY KEY,
    customer_id   INT,
    product_name  TEXT,
    status        VARCHAR(50),
    order_date    TIMESTAMP,
    delivery_date TIMESTAMP
);

CREATE TABLE IF NOT EXISTS complaints (
    complaint_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id  INT,
    order_id     INT,
    issue        TEXT,
    status       VARCHAR(50),
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Long-Term Memory table (key is a reserved word — use backticks)
CREATE TABLE IF NOT EXISTS customer_memory (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    `key`       TEXT,
    value       TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- 2. SEED DATA (aligned with 11 test cases)
-- ==========================================

-- Customers
INSERT IGNORE INTO customers (customer_id, name, email) VALUES
    (1, 'Alice Smith',   'alice@example.com'),
    (2, 'Bob Johnson',   'bob@example.com'),
    (3, 'Charlie Davis', 'charlie@example.com');

-- Orders
-- 12345 → Test 1 (intent parsing): Alice, Wireless Mouse, shipped
-- 1001  → Test 2 (OrderLookup):    Bob, Mechanical Keyboard, processing
-- 5678  → Test 4 (RefundTool):     Alice, Headphones, delivered
-- 2222  → Test 5 (Complaint):      Charlie, Ergonomic Chair, delivered
-- 7890  → Test 6 (multi-step):     Bob, USB-C Hub, delivered
INSERT IGNORE INTO orders (order_id, customer_id, product_name, status, order_date, delivery_date) VALUES
    (12345, 1, 'Wireless Mouse',             'shipped',    '2024-10-01 10:00:00', NULL),
    (1001,  2, 'Mechanical Keyboard',        'processing', '2024-10-25 14:30:00', NULL),
    (5678,  1, 'Noise Cancelling Headphones','delivered',  '2024-09-15 09:00:00', '2024-09-18 12:00:00'),
    (2222,  3, 'Ergonomic Chair',            'delivered',  '2024-08-20 11:15:00', '2024-08-25 16:45:00'),
    (7890,  2, 'USB-C Hub',                  'delivered',  '2024-10-20 08:20:00', '2024-10-22 10:10:00');

-- Pre-seeded Long-Term Memory
-- Test 8/10: Charlie has a history of late deliveries
-- Test 9:    Alice preference (also pre-seeded as baseline)
INSERT IGNORE INTO customer_memory (customer_id, `key`, value) VALUES
    (1, 'resolution_preference', 'prefers refunds over store credit'),
    (3, 'past_issues',           'frequent late deliveries');
