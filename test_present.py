import asyncio
from winrt.windows.devices.enumeration import DeviceInformation
from winrt.windows.devices.bluetooth import BluetoothDevice

async def test():
    aqs = BluetoothDevice.get_device_selector()
    # AQS string to only return devices currently present
    aqs_present = aqs + ' AND System.Devices.Aep.IsPresent:=System.StructuredQueryType.Boolean#True'
    
    try:
        devices = await DeviceInformation.find_all_async_aqs_filter(aqs_present)
        print(f"Found {devices.size} present devices with AQS.")
        for d in devices:
            print(f"Present Device: {d.name}")
            
        print("---")
        # Also run without IsPresent to compare
        all_devices = await DeviceInformation.find_all_async_aqs_filter(aqs)
        print(f"Found {all_devices.size} total paired/cached devices.")
        for d in all_devices:
            print(f"Any Device: {d.name}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
