
# ===================================
# 1. IMPORT LIBRARIES
# ===================================

from faster_whisper import WhisperModel


# ===================================
# 2. LOAD WHISPER MODEL
# ===================================

# Load a lightweight speech recognition model.
# Use CPU inference with INT8 quantization.

print("[STT] Loading Whisper model...")

model = WhisperModel(
    "tiny",
    device="cpu",
    compute_type="int8"
)

print("[STT] Model loaded successfully.")


# ===================================
# 3. TRANSCRIBE AUDIO
# ===================================

def transcribe_audio(filename):

    print("[STT] Transcribing audio...")

    # Convert the recorded speech into text.

    segments, info = model.transcribe(
        str(filename),
        language="en",
        beam_size=1,
        vad_filter=True
    )

    # Combine the transcribed segments
    # into one complete sentence.

    text = " ".join(
        segment.text.strip()
        for segment in segments
    )

    print("[STT] Transcription:", text)

    return text


# ===================================
# 4. TEST SPEECH RECOGNITION
# ===================================

if __name__ == "__main__":

    text = transcribe_audio("customer.wav")

    print("Customer:", text)
