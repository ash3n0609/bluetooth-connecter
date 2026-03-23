from bleak import BleakScanner
import sys

async def scan_devices():
    device_list = []
    seen_macs = set()
    
    if sys.platform == "win32":
        try:
            from winrt.windows.devices.enumeration import DeviceInformation
            from winrt.windows.devices.bluetooth import BluetoothDevice
            
            aqs = BluetoothDevice.get_device_selector()
            aqs += ' AND System.Devices.Aep.IsPresent:=System.StructuredQueryType.Boolean#True'
            classic_devices = await DeviceInformation.find_all_async_aqs_filter(aqs)
            
            for d in classic_devices:
                bt_device = await BluetoothDevice.from_id_async(d.id)
                if bt_device:
                    mac_int = bt_device.bluetooth_address
                    mac_str = ":".join(f"{mac_int:012X}"[i:i+2] for i in range(0, 12, 2))
                    name = d.name or bt_device.name
                    
                    if name and name.strip():
                        seen_macs.add(mac_str)
                        device_list.append({
                            "name": name,
                            "address": mac_str,
                            "rssi": -50,
                            "type": "Classic BT",
                            "ip": None # Placeholder per requirements
                        })
        except Exception as e:
            print(f"Error finding Classic devices: {e}")

    try:
        devices = await BleakScanner.discover(timeout=5.0, return_adv=True)
        for d, adv in devices.values():
            if d.address in seen_macs:
                continue
                
            actual_name = d.name or adv.local_name
            if not actual_name or str(actual_name).strip() == "":
                actual_name = f"Unknown Device ({d.address})"
                
            device_list.append({
                "name": actual_name,
                "address": d.address,
                "rssi": adv.rssi if adv.rssi is not None else -100,
                "type": "BLE",
                "ip": None # Placeholder per requirements
            })
    except Exception as e:
        print(f"BLE Scan Error: {e}")

    # Sort strongest signals first
    device_list.sort(key=lambda x: -x["rssi"])
    return {"status": "success", "devices": device_list}
