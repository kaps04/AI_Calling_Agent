
# ===================================
# 1. IMPORT LIBRARIES
# ===================================

import re


# ===================================
# 2. DEFINE NUMBER WORDS
# ===================================

# Map spoken number words to numeric digits.

NUMBER_WORDS = {
    "zero": "0",
    "oh": "0",
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9"
}


# ===================================
# 3. NORMALIZE SPOKEN ORDER ID
# ===================================

def normalize_order_id(text):

    # Convert text into lowercase and
    # remove unnecessary spaces.

    cleaned = text.lower().strip()

    # Normalize apostrophes.

    cleaned = cleaned.replace("’", "'")

    # Remove sentence punctuation.

    cleaned = cleaned.strip(".,!?")

    # Remove common introductory phrases.

    cleaned = re.sub(
        r"^(my order id is|my order number is|"
        r"it is|it's|order number|order id|order)\s+",
        "",
        cleaned
    )


    # -----------------------------------
    # HANDLE NUMERIC ORDER IDS
    # -----------------------------------

    # Examples:
    # 102, ORD-102, ORD 102

    match = re.fullmatch(
        r"(?:ord[\s-]*)?(\d+)",
        cleaned
    )

    if match:

        return "ORD-" + match.group(1)


    # -----------------------------------
    # REMOVE SPOKEN ORD PREFIX
    # -----------------------------------

    cleaned = re.sub(
        r"^(?:ord[\s-]+|o\s+r\s+d\s+)",
        "",
        cleaned
    )

    # Handle numeric IDs after removing the prefix.

    if cleaned.isdigit():

        return "ORD-" + cleaned


    # -----------------------------------
    # HANDLE HUNDRED-BASED NUMBERS
    # -----------------------------------

    # Example: one hundred and two.

    match = re.fullmatch(
        r"(one|two|three|four|five|six|"
        r"seven|eight|nine) hundred"
        r"(?: (?:and )?"
        r"(one|two|three|four|five|six|"
        r"seven|eight|nine))?",
        cleaned
    )

    if match:

        # Convert the hundreds portion.

        number = int(
            NUMBER_WORDS[match.group(1)]
        ) * 100

        # Add the remaining digit.

        if match.group(2):

            number += int(
                NUMBER_WORDS[match.group(2)]
            )

        return "ORD-" + str(number)


    # -----------------------------------
    # HANDLE INDIVIDUALLY SPOKEN DIGITS
    # -----------------------------------

    # Example: one zero two.

    words = cleaned.split()

    # Check whether every word represents a digit.

    if words and all(
        word in NUMBER_WORDS for word in words
    ):

        number = "".join(
            NUMBER_WORDS[word]
            for word in words
        )

        return "ORD-" + number


    # -----------------------------------
    # RETURN ORIGINAL MESSAGE
    # -----------------------------------

    # If the text cannot be recognized as an
    # order ID, preserve the original message.

    return text


# ===================================
# 4. TEST ORDER ID NORMALIZATION
# ===================================

if __name__ == "__main__":

    print("Spoken Order ID Normalization")
    print("Type 'exit' to stop.")

    while True:

        text = input("\nEnter text: ").strip()

        if text.lower() == "exit":
            break

        if not text:
            continue

        # Normalize the supplied text.

        result = normalize_order_id(text)

        print("[ORIGINAL]", text)

        print("[NORMALIZED]", result)
