import ollama
from tools import get_order_status

order_id = "ORD-102"

status = get_order_status(order_id)

response = ollama.chat(
    model="qwen2.5:1.5b",
    messages=[
        {
            "role": "system",
            "content": """
            You are a customer support assistant.
            Answer only using the provided business information.
            Do not invent information.
            Keep responses short and conversational.
            """
        },
        {
            "role": "user",
            "content": f"""
            Customer question: Where is my order?
            Order ID: {order_id}
            Actual order status: {status}
            """
        }
    ],
    options={"temperature": 0}
)

print(response["message"]["content"])