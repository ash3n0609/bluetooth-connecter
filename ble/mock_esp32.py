"""
mock_esp32.py
─────────────
Simulates the data packet that a real ESP32 would send over BLE.

The mock packet:
  • 50 float32 values (200 bytes) – fake accelerometer / sensor readings
  • Serialised with numpy.save() into a BytesIO buffer so it is a valid
    .npy file that can be loaded with numpy.load() on the receiving end.

Usage
-----
    from ble.mock_esp32 import generate_mock_packet, MOCK_MAC

    raw_bytes = generate_mock_packet()   # bytes, ready to write to disk
"""

import io
import math
import os
import time

import numpy as np

# The MAC address that scanner.py injects as the fake ESP32
MOCK_MAC = "FF:FF:FF:FF:FF:FF"

# ── How many samples the mock ESP32 transmits ─────────────────────────────────
NUM_SAMPLES = 50
SAMPLE_RATE_HZ = 100  # simulated 100 Hz accelerometer


def generate_mock_packet() -> bytes:
    """
    Returns a valid .npy-format byte string containing a (50,) float32 array.

    The values are a sine wave with a small noise component – realistic
    for an accelerometer / vibration sensor on an ESP32.
    """
    t = np.linspace(0, NUM_SAMPLES / SAMPLE_RATE_HZ, NUM_SAMPLES, dtype=np.float32)
    signal = (
        np.sin(2 * math.pi * 10 * t)          # 10 Hz primary tone
        + 0.3 * np.sin(2 * math.pi * 35 * t)  # 35 Hz harmonic
        + 0.05 * np.random.randn(NUM_SAMPLES).astype(np.float32)  # sensor noise
    ).astype(np.float32)

    buf = io.BytesIO()
    np.save(buf, signal)
    return buf.getvalue()


def save_mock_packet(directory: str = "downloads") -> str:
    """
    Generates a mock packet and saves it to *directory* as a .npy file.

    Returns the absolute path of the saved file.
    """
    os.makedirs(directory, exist_ok=True)
    filename = f"mock_esp32_{int(time.time())}.npy"
    filepath = os.path.join(directory, filename)

    data = generate_mock_packet()
    with open(filepath, "wb") as f:
        f.write(data)

    return filepath
