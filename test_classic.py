import asyncio
from winrt.windows.devices.enumeration import DeviceInformation
from winrt.windows.devices.bluetooth import BluetoothDevice

async def find_classic():
    # AQS for classic Bluetooth
    aqs = BluetoothDevice.get_device_selector()
    devices = await DeviceInformation.find_all_async_aqs_filter(aqs)
    
    print(f"Found {devices.size} devices")
    for d in devices:
        try:
            bt_device = await BluetoothDevice.from_id_async(d.id)
            if bt_device:
                print(f"Name: {bt_device.name}, Address: {bt_device.bluetooth_address:X}")
        except Exception as e:
            print(f"Error for {d.name}: {e}")

if __name__ == "__main__":
    asyncio.run(find_classic())
