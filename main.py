import asyncio
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from bleak import BleakScanner, BleakClient
from winrt.windows.devices.enumeration import DeviceInformation
from winrt.windows.devices.bluetooth import BluetoothDevice

app = FastAPI(title="Bluetooth Manager")

# Mount static files (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates for HTML rendering
templates = Jinja2Templates(directory="templates")

# Store connected clients to easily disconnect them later
connected_clients = {}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/scan")
async def scan_devices():
    """Scans for nearby BLE and Classic devices and returns a list."""
    try:
        device_list = []
        seen_macs = set()
        
        # 1. Provide an initial list from Classic Bluetooth cache (for phones/headphones)
        try:
            aqs = BluetoothDevice.get_device_selector()
            # Append AQS rule to only return devices currently present (nearby/turned on)
            aqs += ' AND System.Devices.Aep.IsPresent:=System.StructuredQueryType.Boolean#True'
            classic_devices = await DeviceInformation.find_all_async_aqs_filter(aqs)
            for d in classic_devices:
                bt_device = await BluetoothDevice.from_id_async(d.id)
                if bt_device:
                    mac_int = bt_device.bluetooth_address
                    mac_str = ":".join(f"{mac_int:012X}"[i:i+2] for i in range(0, 12, 2))
                    # Prefer the Windows friendly name over the hardware ad name
                    name = d.name or bt_device.name
                    
                    if name and name.strip():
                        seen_macs.add(mac_str)
                        device_list.append({
                            "name": name,
                            "address": mac_str,
                            "rssi": -50, # Fake strong RSSI for known devices so they show up high
                            "type": "Classic"
                        })
        except Exception as e:
            print(f"Error finding Classic Bluetooth devices: {e}")

        # 2. Scan for BLE devices, timeout 5 seconds
        devices = await BleakScanner.discover(timeout=5.0, return_adv=True)
        for d, adv in devices.values():
            if d.address in seen_macs:
                continue # We already have a good name from the Classic side
                
            # Get name from either standard property or advertisement data
            actual_name = d.name or adv.local_name
            # Provide a fallback if name is completely empty, incorporating the MAC address so it's distinct
            if not actual_name or str(actual_name).strip() == "":
                actual_name = f"Unknown Device ({d.address})"
                
            device_list.append({
                "name": actual_name,
                "address": d.address,
                "rssi": adv.rssi if adv.rssi is not None else -100,
                "type": "BLE"
            })
            seen_macs.add(d.address)
        
        # Sort by signal strength (RSSI)
        device_list.sort(key=lambda x: x["rssi"], reverse=True)
        return {"status": "success", "devices": device_list}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/connect/{address}")
async def connect_device(address: str):
    """Attempt to connect to a specific BLE device."""
    if address in connected_clients and connected_clients[address].is_connected:
        return {"status": "success", "message": "Already connected to device"}
        
    try:
        client = BleakClient(address)
        await client.connect(timeout=10.0)
        
        if client.is_connected:
            connected_clients[address] = client
            return {"status": "success", "message": f"Connected to {address}"}
        else:
            return {"status": "error", "message": "Connection failed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/disconnect/{address}")
async def disconnect_device(address: str):
    """Disconnect from a BLE device."""
    if address in connected_clients:
        client = connected_clients[address]
        if client.is_connected:
            await client.disconnect()
            del connected_clients[address]
            return {"status": "success", "message": f"Disconnected from {address}"}
    return {"status": "error", "message": "Not connected to this device"}
