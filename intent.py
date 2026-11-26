
# ===================================
# 1. IMPORT LIBRARIES
# ===================================

import re
import ollama


# ===================================
# 2. DEFINE LLM CONFIGURATION
# ===================================

MODEL = "qwen2.5:1.5b"


# ===================================
# 3. DEFINE VALID INTENTS
# ===================================

VALID_INTENTS = [
    "order_status",
    "refund",
    "business_hours",
    "human_support",
    "general",
    "chitchat",
    "clarification"
]


# ===================================
# 4. DEFINE COMMON CONVERSATION WORDS
# ===================================

# Handle common greetings and casual conversation
# without calling the LLM.

CHITCHAT_MESSAGES = {
    "hi",
    "hello",
    "hey",
    "good morning",
    "good afternoon",
    "good evening",
    "how are you",
    "nice to meet you",
    "thank you",
    "thanks",
    "thank you very much",
    "goodbye",
    "bye",
    "see you",
    "okay",
    "ok"
}


# Handle common incomplete messages.

CLARIFICATION_MESSAGES = {
    "something",
    "what",
    "yes",
    "no",
    "help",
    "i need help",
    "i have a question",
    "asdf",
    "asdfgh"
}


# ===================================
# 5. RULE-BASED CLASSIFICATION
# ===================================

def rule_based_intent(message):

    # Convert the message into lowercase.

    cleaned = message.lower().strip()

    # Remove punctuation and extra spaces.

    cleaned = cleaned.strip(".,!?")

    cleaned = " ".join(cleaned.split())

    # Handle empty messages.

    if not cleaned:

        return "clarification"


    # -----------------------------------
    # DETECT CASUAL CONVERSATION
    # -----------------------------------

    if cleaned in CHITCHAT_MESSAGES:

        return "chitchat"


    # -----------------------------------
    # DETECT UNCLEAR MESSAGES
    # -----------------------------------

    if cleaned in CLARIFICATION_MESSAGES:

        return "clarification"


    # -----------------------------------
    # DETECT EXPLICIT ORDER IDS
    # -----------------------------------

    if re.fullmatch(r"ord-\d+", cleaned):

        return "order_status"


    # -----------------------------------
    # DETECT STANDALONE NUMBERS
    # -----------------------------------

    # Without conversation context, a number
    # alone does not establish an intent.

    if cleaned.isdigit():

        return "clarification"


    # No rule matched.
    # Use the LLM for classification.

    return None


# ===================================
# 6. DEFINE CLASSIFICATION PROMPT
# ===================================

SYSTEM_PROMPT = """
Classify the customer message into exactly one label.

order_status:
Tracking or checking a specific order.

refund:
Refunds, returns or cancellations.

business_hours:
Opening hours and customer support availability.

human_support:
Requests to speak to a human or manager.

general:
Clear business questions about products,
payment methods, shipping policies or services.

chitchat:
Greetings, thanks, farewells and casual conversation.

clarification:
Unclear, incomplete or meaningless messages.

Examples:

Where is my order? -> order_status
I want my money back -> refund
When do you open? -> business_hours
Connect me with a human -> human_support
Do you accept PayPal? -> general
How much does shipping cost? -> general
Hello -> chitchat
Nice to meet you -> chitchat
I need help -> clarification
adsfr -> clarification
xyzabc -> clarification
500 -> clarification

Return only the category label.
Do not repeat the customer message.
Do not explain.
Do not answer the customer question.
"""


# ===================================
# 7. CLASSIFY CUSTOMER INTENT
# ===================================

def classify_intent(message):

    # First attempt rule-based classification.

    rule_intent = rule_based_intent(message)

    if rule_intent is not None:

        print("[RULE] Detected intent:", rule_intent)

        return rule_intent


    # -----------------------------------
    # LLM-BASED CLASSIFICATION
    # -----------------------------------

    print("[LLM] Classifying customer message...")

    response = ollama.chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": message
            }
        ],
        options={
            "temperature": 0,
            "num_predict": 16
        }
    )


    # -----------------------------------
    # NORMALIZE LLM OUTPUT
    # -----------------------------------

    intent = response["message"]["content"]

    intent = intent.strip().lower()

    intent = intent.strip("`'\".! ")


    # -----------------------------------
    # VALIDATE LLM OUTPUT
    # -----------------------------------

    if intent in VALID_INTENTS:

        return intent


    # If the model generates an invalid category,
    # request clarification instead of using RAG.

    print("[WARNING] Invalid intent:", intent)

    return "clarification"


# ===================================
# 8. TEST INTENT CLASSIFICATION
# ===================================

if __name__ == "__main__":

    print("Hybrid AI Intent Classification System")
    print("Model:", MODEL)
    print("Type 'exit' to stop.")

    while True:

        message = input("\nCustomer: ").strip()

        if message.lower() == "exit":

            break

        intent = classify_intent(message)

        print("[INTENT]", intent)
