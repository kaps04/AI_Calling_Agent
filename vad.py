
# ===================================
# 1. IMPORT LIBRARIES
# ===================================

import numpy as np


# ===================================
# 2. DEFINE SPEECH THRESHOLD
# ===================================

# Audio energy above or equal to this value
# is considered potential speech.

ENERGY_THRESHOLD = 500


# ===================================
# 3. CALCULATE AUDIO ENERGY
# ===================================

def calculate_energy(audio_chunk):

    # Convert integer audio samples into
    # floating-point numbers to avoid overflow.

    audio = audio_chunk.astype(np.float32)

    # Calculate Root Mean Square (RMS).

    energy = np.sqrt(np.mean(audio ** 2))

    return float(energy)


# ===================================
# 4. DETECT SPEECH
# ===================================

def is_speech(audio_chunk, threshold=ENERGY_THRESHOLD):

    # Calculate the energy of the audio segment.

    energy = calculate_energy(audio_chunk)

    # Compare audio energy with the threshold.

    return energy >= threshold


# ===================================
# 5. TEST VOICE ACTIVITY DETECTION
# ===================================

if __name__ == "__main__":

    print("Voice Activity Detection Test")
    print("Energy Threshold:", ENERGY_THRESHOLD)

    # Generate synthetic audio samples.

    silence = np.zeros(480)
    speech = np.full(480, 1000)

    # Test silence detection.

    print("\n[TEST 1] Silence")
    print("Audio Energy:", calculate_energy(silence))
    print("Speech Detected:", is_speech(silence))

    # Test speech detection.

    print("\n[TEST 2] Speech")
    print("Audio Energy:", calculate_energy(speech))
    print("Speech Detected:", is_speech(speech))
