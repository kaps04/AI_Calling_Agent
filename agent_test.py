
import ollama

from tools import get_order_status

# Customer's order ID
order_id = "ORD-102"

# Retrieve actual business information
status = get_order_status(order_id)

# Send information to the LLM
response = ollama.chat(
    model="qwen2.5:1.5b",
    messages=[
        {
            "role": "system",
            "content": """
            You are a customer support assistant.
            Answer using only the provided business information.
            Do not invent additional information.
            Keep your response short and conversational.
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
    ]
)

print(response["message"]["content"])
