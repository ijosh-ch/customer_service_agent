import mysql.connector

def setup_database():
    try:
        # 1. Connect to MySQL server (no database yet)
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="12345678"
        )

        cursor = conn.cursor()

        # 2. Create database if it doesn't exist
        cursor.execute("CREATE DATABASE IF NOT EXISTS customer_db")
        print("Database checked/created: customer_db")

        # 3. Switch to database
        cursor.execute("USE customer_db")

        # 4. Define tables
        tables = {
            "customers": """
                CREATE TABLE IF NOT EXISTS customers (
                    customer_id INT PRIMARY KEY AUTO_INCREMENT,
                    name VARCHAR(255),
                    email VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,

            "orders": """
                CREATE TABLE IF NOT EXISTS orders (
                    order_id INT PRIMARY KEY AUTO_INCREMENT,
                    customer_id INT,
                    product_name VARCHAR(255),
                    status VARCHAR(50),
                    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    delivery_date TIMESTAMP
                )
            """,

            "complaints": """
                CREATE TABLE IF NOT EXISTS complaints (
                    complaint_id INT PRIMARY KEY AUTO_INCREMENT,
                    customer_id INT,
                    order_id INT,
                    issue TEXT,
                    status VARCHAR(50) DEFAULT 'open',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,

            "customer_memory": """
                CREATE TABLE IF NOT EXISTS customer_memory (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    customer_id INT,
                    key_name VARCHAR(255),
                    value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
        }

        # 5. Create tables
        for table_name, schema in tables.items():
            print(f"Creating table: {table_name}")
            cursor.execute(schema)

        # 6. Save changes
        conn.commit()

        print("\nSUCCESS: All tables created successfully!")

    except mysql.connector.Error as err:
        print("ERROR:", err)

    finally:
        print("Inserting mock data...")

        cursor.execute("""
        INSERT INTO customers (customer_id, name, email)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
        name = VALUES(name),
        email = VALUES(email)
        """, (1001, 'Alice Smith', 'alice@example.com'))


        cursor.execute("""
        INSERT INTO orders (order_id, customer_id, product_name, status)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        product_name = VALUES(product_name),
        status = VALUES(status)
        """, (12345, 1001, 'Wireless Mouse', 'shipped'))


        cursor.execute("""
        INSERT INTO orders (order_id, customer_id, product_name, status)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        product_name = VALUES(product_name),
        status = VALUES(status)
        """, (7890, 1001, 'Mechanical Keyboard', 'delivered'))


        cursor.execute("""
        INSERT INTO orders (order_id, customer_id, product_name, status)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        product_name = VALUES(product_name),
        status = VALUES(status)
        """, (5678, 1001, 'Monitor', 'delivered'))

        conn.commit()
        print("Mock data inserted successfully!")

        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()
            print("Connection closed")

if __name__ == "__main__":
    setup_database()