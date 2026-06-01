"""
setup_db.py — Initialize and seed the MySQL database for the Customer Service Agent.

Works with both local MySQL and the lab remote server.

Usage:
  # Local MySQL (create DB + user + tables + seed)
  python setup_db.py --local

  # Local MySQL with custom credentials
  python setup_db.py --host localhost --port 3306 --admin-user root --admin-password secret --db customer_service

  # Remote lab server (tables + seed only — DB already exists)
  python setup_db.py --host 140.118.122.119 --user llm-student --password llm12345 --db llm-course

  # Reset (truncate all tables and re-seed)
  python setup_db.py --local --reset

  # Use values from .env
  python setup_db.py --from-env
"""

import argparse
import os
import sys

try:
    import mysql.connector
    from mysql.connector import errorcode
except ImportError:
    print("ERROR: mysql-connector-python is not installed.")
    print("  Run: pip install mysql-connector-python")
    sys.exit(1)


# ==========================================
# SCHEMA
# ==========================================

TABLES = {
    "customers": """
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INT PRIMARY KEY,
            name        VARCHAR(100),
            email       VARCHAR(100),
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    "orders": """
        CREATE TABLE IF NOT EXISTS orders (
            order_id      INT PRIMARY KEY,
            customer_id   INT,
            product_name  TEXT,
            status        VARCHAR(50),
            order_date    TIMESTAMP,
            delivery_date TIMESTAMP
        )
    """,
    "complaints": """
        CREATE TABLE IF NOT EXISTS complaints (
            complaint_id INT AUTO_INCREMENT PRIMARY KEY,
            customer_id  INT,
            order_id     INT,
            issue        TEXT,
            status       VARCHAR(50),
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    "customer_memory": """
        CREATE TABLE IF NOT EXISTS customer_memory (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            customer_id INT,
            `key`       TEXT,
            value       TEXT,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
}

# ==========================================
# SEED DATA (aligned with 11 test cases)
# ==========================================

SEED_CUSTOMERS = [
    (1, "Alice Smith",   "alice@example.com"),
    (2, "Bob Johnson",   "bob@example.com"),
    (3, "Charlie Davis", "charlie@example.com"),
]

SEED_ORDERS = [
    # (order_id, customer_id, product_name, status, order_date, delivery_date)
    # Test 1 — Intent Parsing: Alice, order 12345, shipped
    (12345, 1, "Wireless Mouse",              "shipped",    "2024-10-01 10:00:00", None),
    # Test 2 — OrderLookupTool: Bob, order 1001, processing
    (1001,  2, "Mechanical Keyboard",         "processing", "2024-10-25 14:30:00", None),
    # Test 4 — RefundTool: Alice, order 5678, delivered
    (5678,  1, "Noise Cancelling Headphones", "delivered",  "2024-09-15 09:00:00", "2024-09-18 12:00:00"),
    # Test 5 — Complaint: Charlie, order 2222, delivered
    (2222,  3, "Ergonomic Chair",             "delivered",  "2024-08-20 11:15:00", "2024-08-25 16:45:00"),
    # Test 6 — Multi-step: Bob, order 7890, delivered
    (7890,  2, "USB-C Hub",                   "delivered",  "2024-10-20 08:20:00", "2024-10-22 10:10:00"),
]

SEED_MEMORY = [
    # Test 8/10 — Charlie has a history of late deliveries
    (3, "past_issues",            "frequent late deliveries"),
    # Test 9   — Alice preference (pre-seeded baseline)
    (1, "resolution_preference",  "prefers refunds over store credit"),
]


# ==========================================
# HELPERS
# ==========================================

def connect(host, port, user, password, database=None):
    kwargs = dict(host=host, port=port, user=user, password=password)
    if database:
        kwargs["database"] = database
    return mysql.connector.connect(**kwargs)


def create_database(cursor, db_name):
    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        print(f"  Database `{db_name}` ready.")
    except mysql.connector.Error as err:
        print(f"  ERROR creating database: {err}")
        raise


def create_user_and_grant(cursor, db_name, new_user, new_password):
    try:
        cursor.execute(
            f"CREATE USER IF NOT EXISTS '{new_user}'@'%' IDENTIFIED BY '{new_password}';"
        )
        cursor.execute(
            f"GRANT ALL PRIVILEGES ON `{db_name}`.* TO '{new_user}'@'%';"
        )
        cursor.execute("FLUSH PRIVILEGES;")
        print(f"  User '{new_user}'@'%' ready with full grants on `{db_name}`.")
    except mysql.connector.Error as err:
        print(f"  ERROR creating user: {err}")
        raise


def create_tables(cursor):
    for name, ddl in TABLES.items():
        cursor.execute(ddl)
        print(f"  Table `{name}` ready.")


def truncate_tables(cursor):
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    for name in ["customer_memory", "complaints", "orders", "customers"]:
        cursor.execute(f"TRUNCATE TABLE `{name}`;")
        print(f"  Truncated `{name}`.")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")


def seed_data(cursor, conn):
    cursor.executemany(
        "INSERT IGNORE INTO customers (customer_id, name, email) VALUES (%s, %s, %s);",
        SEED_CUSTOMERS,
    )
    print(f"  Seeded {cursor.rowcount} customers.")

    rows_with_nulls = [
        (r[0], r[1], r[2], r[3], r[4], r[5]) for r in SEED_ORDERS
    ]
    cursor.executemany(
        "INSERT IGNORE INTO orders "
        "(order_id, customer_id, product_name, status, order_date, delivery_date) "
        "VALUES (%s, %s, %s, %s, %s, %s);",
        rows_with_nulls,
    )
    print(f"  Seeded {cursor.rowcount} orders.")

    cursor.executemany(
        "INSERT IGNORE INTO customer_memory (customer_id, `key`, value) VALUES (%s, %s, %s);",
        SEED_MEMORY,
    )
    print(f"  Seeded {cursor.rowcount} customer_memory rows.")

    conn.commit()


def verify(cursor):
    print()
    print("  Verification:")
    for table in ["customers", "orders", "complaints", "customer_memory"]:
        cursor.execute(f"SELECT COUNT(*) FROM `{table}`;")
        count = cursor.fetchone()[0]
        print(f"    {table}: {count} rows")


# ==========================================
# MAIN
# ==========================================

def main():
    parser = argparse.ArgumentParser(description="Initialize and seed the Customer Service Agent database.")
    parser.add_argument("--host",           default=None,  help="MySQL host")
    parser.add_argument("--port",           default=3306,  type=int, help="MySQL port (default: 3306)")
    parser.add_argument("--user",           default=None,  help="MySQL user (must already exist)")
    parser.add_argument("--password",       default=None,  help="MySQL password")
    parser.add_argument("--db",             default=None,  help="Database name")
    parser.add_argument("--admin-user",     default=None,  help="Admin user for DB+user creation (local only)")
    parser.add_argument("--admin-password", default=None,  help="Admin password for DB+user creation (local only)")
    parser.add_argument("--local",          action="store_true",
                        help="Shortcut for local MySQL: creates DB and user 'llm-student' with defaults")
    parser.add_argument("--from-env",       action="store_true",
                        help="Read DB_HOST / DB_USER / DB_PASSWORD / DB_NAME from environment / .env file")
    parser.add_argument("--reset",          action="store_true",
                        help="Truncate all tables before seeding (re-seed from scratch)")
    parser.add_argument("--create-user",    action="store_true",
                        help="Create DB + llm-student user (requires --admin-user / --admin-password)")
    args = parser.parse_args()

    # Load .env if present
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    # Resolve connection params
    if args.local:
        host           = "localhost"
        port           = 3306
        admin_user     = args.admin_user or "root"
        admin_password = args.admin_password or input("Enter MySQL root password: ")
        db_name        = args.db or "customer_service"
        user           = args.user or "llm-student"
        password       = args.password or "llm12345"
        create_user    = True
    elif args.from_env:
        host     = os.getenv("DB_HOST", "140.118.122.119")
        port     = int(os.getenv("DB_PORT", "3306"))
        user     = os.getenv("DB_USER", "llm-student")
        password = os.getenv("DB_PASSWORD", "llm12345")
        db_name  = os.getenv("DB_NAME", "llm-course")
        create_user = False
        admin_user = admin_password = None
    else:
        host     = args.host     or os.getenv("DB_HOST", "140.118.122.119")
        port     = args.port     or int(os.getenv("DB_PORT", "3306"))
        user     = args.user     or os.getenv("DB_USER", "llm-student")
        password = args.password or os.getenv("DB_PASSWORD", "llm12345")
        db_name  = args.db       or os.getenv("DB_NAME", "llm-course")
        create_user    = args.create_user
        admin_user     = args.admin_user
        admin_password = args.admin_password

    print("=" * 60)
    print("  Customer Service Agent — Database Setup")
    print("=" * 60)
    print(f"  Host    : {host}:{port}")
    print(f"  Database: {db_name}")
    print(f"  User    : {user}")
    print()

    # Step 1: Create DB + user (local / admin flow)
    if create_user:
        print("Step 1: Creating database and user...")
        try:
            admin_conn = connect(host, port, admin_user, admin_password)
            admin_conn.autocommit = True
            admin_cur = admin_conn.cursor()
            create_database(admin_cur, db_name)
            create_user_and_grant(admin_cur, db_name, user, password)
            admin_cur.close()
            admin_conn.close()
        except mysql.connector.Error as err:
            print(f"\nERROR: Could not connect as admin user '{admin_user}': {err}")
            print("  Check that MySQL is running and the admin password is correct.")
            sys.exit(1)
    else:
        print("Step 1: Skipping DB/user creation (using existing credentials).")

    # Step 2: Connect as the app user
    print("\nStep 2: Connecting to database...")
    try:
        conn = connect(host, port, user, password, db_name)
        conn.autocommit = False
        cursor = conn.cursor()
        print(f"  Connected as '{user}'@{host}.")
    except mysql.connector.Error as err:
        print(f"\nERROR: Cannot connect as '{user}': {err}")
        sys.exit(1)

    # Step 3: Create tables
    print("\nStep 3: Creating tables...")
    create_tables(cursor)

    # Step 4: Optionally truncate
    if args.reset:
        print("\nStep 4: Resetting (truncating) all tables...")
        truncate_tables(cursor)
    else:
        print("\nStep 4: Skipping truncate (use --reset to wipe and re-seed).")

    # Step 5: Seed
    print("\nStep 5: Seeding data...")
    seed_data(cursor, conn)

    # Step 6: Verify
    print("\nStep 6: Verifying row counts...")
    verify(cursor)

    cursor.close()
    conn.close()

    print()
    print("=" * 60)
    print("  Setup complete.")
    print(f"  Update your .env:")
    print(f"    DB_HOST={host}")
    print(f"    DB_PORT={port}")
    print(f"    DB_USER={user}")
    print(f"    DB_PASSWORD={password}")
    print(f"    DB_NAME={db_name}")
    print("=" * 60)


if __name__ == "__main__":
    main()
