import asyncio
from bleak import BleakClient

DEVICE_NAME_UUID = "00002a00-0000-1000-8000-00805f9b34fb"

# The closest device
ADDRESS = "2A:76:F9:A7:9E:36"

async def test_gatt():
    print(f"Attempting GATT connection to {ADDRESS}...")
    try:
        async with BleakClient(ADDRESS, timeout=8.0) as client:
            print(f"Connected: {client.is_connected}")
            try:
                data = await asyncio.wait_for(
                    client.read_gatt_char(DEVICE_NAME_UUID), timeout=5.0
                )
                print(f"Device Name: {data.decode('utf-8', errors='ignore')}")
            except Exception as e:
                print(f"Name characteristic error: {e}")

            print("Services:")
            for svc in client.services:
                print(f"  {svc}")
    except Exception as e:
        print(f"Connection error: {e}")

asyncio.run(test_gatt())
