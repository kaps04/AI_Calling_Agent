
import sqlite3

# Connect to the database
conn = sqlite3.connect("business.db")

# Create a cursor
cursor = conn.cursor()

# Create a table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        order_id TEXT PRIMARY KEY,
        customer_name TEXT,
        product TEXT,
        status TEXT
    )
""")

# Sample business data
orders = [
    ("ORD-101", "John", "Laptop", "Delivered"),
    ("ORD-102", "Sarah", "Headphones", "Processing"),
    ("ORD-103", "David", "Monitor", "Shipped"),
    ("ORD-104", "Emily", "Keyboard", "Cancelled"),
    ("ORD-105", "Michael", "Mouse", "Shipped")
]

# Insert data into the table
cursor.executemany("""
    INSERT OR IGNORE INTO orders
    VALUES (?, ?, ?, ?)
""", orders)

# Save changes
conn.commit()

# Close the connection
conn.close()

print("Database created successfully!")
