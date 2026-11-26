
import sqlite3


def get_order_status(order_id):

    conn = sqlite3.connect("business.db")

    cursor = conn.cursor()

    cursor.execute(
        "SELECT status FROM orders WHERE order_id = ?",
        (order_id.strip().upper(),)
    )

    result = cursor.fetchone()

    conn.close()

    if result:
        return result[0]

    return "Order not found"


# Test the tool independently

if __name__ == "__main__":

    order_id = input("Enter order ID: ")

    status = get_order_status(order_id)

    print("Order status:", status)
