import asyncio
import struct
import numpy as np
from bless import (
    BlessServer,
    BlessGATTCharacteristic,
    GATTCharacteristicProperties,
    GATTAttributePermissions
)

# --- Configuration matching the Web App specifications ---
DEVICE_NAME = "Linux_ECG_Sim"
SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
CHAR_UUID = "abcdef01-1234-5678-1234-56789abcdef0"
DATA_FILE = "ecg_data_1758379673.npy"

# Bless requires dummy read/write functions for the characteristic
def read_request(characteristic: BlessGATTCharacteristic, **kwargs) -> bytearray:
    # Respond with the currently stored value whenever a read request is made
    return characteristic.value

def write_request(characteristic: BlessGATTCharacteristic, value: bytearray, **kwargs):
    # Update the characteristic value if a write request is made
    characteristic.value = value

async def run_ble_server():
    # 1. Load the dataset
    try:
        print(f"Loading ECG data from {DATA_FILE}...")
        ecg_data = np.load(DATA_FILE)
        if len(ecg_data) == 0:
            raise ValueError("ECG data array is empty.")
        print(f"Successfully loaded {len(ecg_data)} data points from {DATA_FILE}.")
    except Exception as e:
        print(f"Error loading ECG data: {e}")
        return

    # 2. Initialize Bless server (Peripheral)
    server = BlessServer(name=DEVICE_NAME, name_overwrite=True)

    # Attach the generic handlers
    server.read_request_func = read_request
    server.write_request_func = write_request

    # 3. Add the main Service
    await server.add_new_service(SERVICE_UUID)

    # Set up characteristic flags to match specification "Permissions: Read and Notify"
    char_flags = (
        GATTCharacteristicProperties.read |
        GATTCharacteristicProperties.notify
    )
    permissions = (
        GATTAttributePermissions.readable
    )

    # Initial value: a 64-bit float 0.0, packed as Little Endian ('<d')
    initial_value = bytearray(struct.pack('<d', 0.0))

    # Add the single Characteristic to the defined service
    await server.add_new_characteristic(
        SERVICE_UUID,
        CHAR_UUID,
        char_flags,
        initial_value,
        permissions
    )

    print(f"Starting BLE Server: {DEVICE_NAME}")
    await server.start()
    print("Server broadcast started successfully. Waiting for connections. Press Ctrl+C to stop.")

    try:
        index = 0
        while True:
            # Get the current float value from numpy array cyclically
            value = float(ecg_data[index % len(ecg_data)])

            # Pack the 64-bit float into 8 raw bytes (Little Endian bytes order)
            packed_value = bytearray(struct.pack('<d', value))

            # Update the characteristic attribute on the server
            server.get_characteristic(CHAR_UUID).value = packed_value

            # Trigger a notification to all subscribed clients
            server.update_value(SERVICE_UUID, CHAR_UUID)

            # Advance index and block for exactly ~100ms
            index += 1
            await asyncio.sleep(0.1)

    except KeyboardInterrupt:
        print("\nStopping BLE Server...")
    except Exception as e:
        print(f"Unexpected error occurred in broadcasting loop: {e}")
    finally:
        await server.stop()
        print("Server completely stopped.")

if __name__ == "__main__":
    asyncio.run(run_ble_server())
