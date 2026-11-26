
import ollama

MODEL = "qwen2.5:1.5b"

VALID_INTENTS = [
    "order_status",
    "refund",
    "business_hours",
    "human_support",
    "general",
    "chitchat"
]


def classify_intent(message):

    response = ollama.chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": """
You are a customer intent classifier.

Classify the message into exactly one category:

order_status: Tracking a specific order or package.

refund: Returns, refunds or money-back inquiries.

business_hours: Opening hours and support availability.

human_support: Requests for a human or manager.

general: Company policies, shipping costs,
payment methods and business information.

chitchat: Greetings, thanks, farewells,
casual conversation or unrelated topics.

Examples:

Hello -> chitchat
Nice to meet you -> chitchat
How are you? -> chitchat
Thank you -> chitchat
Goodbye -> chitchat
Where is my package? -> order_status
Track ORD-102 -> order_status
I want my money back -> refund
Are you open on Sunday? -> business_hours
Do you accept PayPal? -> general
How much does shipping cost? -> general
I want to speak to a manager -> human_support

Return only the category name.
Do not explain your answer.
"""
            },
            {
                "role": "user",
                "content": message
            }
        ],
        options={"temperature": 0}
    )

    intent = response["message"]["content"].strip().lower()

    if intent not in VALID_INTENTS:
        return "general"

    return intent


if __name__ == "__main__":

    while True:

        message = input("\nCustomer: ")

        if message.lower().strip() == "exit":
            break

        print("Detected intent:", classify_intent(message))
