
# ===================================
# 1. IMPORT LIBRARIES
# ===================================
from fastapi.responses import Response

from tts import generate_speech
import requests

from pathlib import Path


# ===================================
# 2. DEFINE CONFIGURATION
# ===================================

URL = "http://127.0.0.1:8000/transcribe"

BASE_DIR = Path(__file__).resolve().parent

AUDIO_FILE = BASE_DIR / "customer.wav"


# ===================================
# 3. TEST SPEECH-TO-TEXT API
# ===================================

def test_transcription():

    # Verify that the audio file exists.

    if not AUDIO_FILE.exists():

        print("[ERROR] Audio file not found")

        return

    print("[TEST] Uploading:", AUDIO_FILE.name)

    try:

        # Open and upload the audio file.

        with open(AUDIO_FILE, "rb") as audio:

            files = {
                "file": (
                    AUDIO_FILE.name,
                    audio,
                    "audio/wav"
                )
            }

            response = requests.post(
                URL,
                files=files,
                timeout=120
            )

        # Check the HTTP response.

        response.raise_for_status()

        # Extract transcription results.

        result = response.json()

        print("[STATUS]", response.status_code)

        print("[TRANSCRIPTION]", result["text"])

        print("[LATENCY]", result["latency"], "seconds")

    except requests.exceptions.RequestException as error:

        print("[ERROR]", error)


# ===================================
# 4. RUN TEST
# ===================================

if __name__ == "__main__":

    test_transcription()
