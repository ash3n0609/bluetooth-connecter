import asyncio
import os

from bleak import BleakClient
from ble.mock_esp32 import MOCK_MAC, save_mock_packet

RECEIVED_DIR = "downloads"
os.makedirs(RECEIVED_DIR, exist_ok=True)


# ── Mock handler ──────────────────────────────────────────────────────────────

async def _handle_mock_device() -> dict:
    """
    Simulates the full BLE receive flow for the mock ESP32.
    Generates a valid .npy packet, saves it to downloads/, and returns
    the same response shape as a real BLE connection.
    """
    print("[Mock] Simulating ESP32 BLE connection…")
    # Simulate slight connection latency
    await asyncio.sleep(1.5)

    filepath = save_mock_packet(RECEIVED_DIR)
    file_size = os.path.getsize(filepath)

    print(f"[Mock] Data saved → {filepath} ({file_size} bytes)")
    return {
        "status": "success",
        "message": f"Mock ESP32 data received and saved ({file_size} bytes). "
                   f"File: {os.path.basename(filepath)}",
        "saved": True,
        "bytes_received": file_size,
        "filename": os.path.basename(filepath),
        "mock": True,
    }


# ── Real BLE receiver ─────────────────────────────────────────────────────────

class BLEReceiver:
    def __init__(self, mac_address):
        self.mac_address = mac_address
        self.client = BleakClient(mac_address, disconnected_callback=self.handle_disconnect)
        self.buffer = bytearray()
        self.is_connected = False
        self.file_saved = False

    def handle_disconnect(self, client):
        print(f"Device {self.mac_address} disconnected.")
        self.is_connected = False
        self.save_data()

    def notification_handler(self, sender, data):
        print(f"Received {len(data)} bytes from {sender}")
        self.buffer.extend(data)

    def save_data(self):
        if len(self.buffer) > 0 and not self.file_saved:
            file_name = f"{self.mac_address.replace(':', '_')}_data.npy"
            file_path = os.path.join(RECEIVED_DIR, file_name)
            with open(file_path, "wb") as f:
                f.write(self.buffer)
            print(f"Data saved to {file_path}")
            self.file_saved = True

    async def connect_and_receive(self, timeout=30):
        try:
            print(f"Attempting to connect to {self.mac_address}...")
            await self.client.connect()
            self.is_connected = True
            print(f"Connected to {self.mac_address}")

            # Find a characteristic that supports notify or indicate
            notify_char = None
            for service in self.client.services:
                for char in service.characteristics:
                    if "notify" in char.properties or "indicate" in char.properties:
                        notify_char = char.uuid
                        break
                if notify_char:
                    break

            if notify_char:
                print(f"Subscribing to {notify_char}")
                await self.client.start_notify(notify_char, self.notification_handler)

                wait_time = 0
                while self.is_connected and wait_time < timeout:
                    await asyncio.sleep(1)
                    wait_time += 1

                if self.is_connected:
                    try:
                        await self.client.stop_notify(notify_char)
                    except Exception as e:
                        print(f"Error stopping notify: {e}")
                    await self.client.disconnect()

                self.save_data()
            else:
                print("No notify/indicate characteristic found!")
                await self.client.disconnect()
                return {"status": "error", "message": "No suitable characteristic found for receiving data."}

            return {
                "status": "success",
                "message": f"Received {len(self.buffer)} bytes.",
                "saved": self.file_saved,
                "bytes_received": len(self.buffer),
            }

        except Exception as e:
            print(f"BLE connection error: {e}")
            return {"status": "error", "message": str(e)}


# ── Public entry point ────────────────────────────────────────────────────────

async def connect_and_receive_ble_data(mac_address: str) -> dict:
    """
    If the target MAC is the injected mock device, return synthetic ESP32 data.
    Otherwise attempt a real BLE connection.
    """
    if mac_address.upper() == MOCK_MAC:
        return await _handle_mock_device()

    receiver = BLEReceiver(mac_address)
    return await receiver.connect_and_receive(timeout=30)

