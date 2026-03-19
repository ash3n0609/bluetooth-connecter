import asyncio
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from bleak import BleakScanner, BleakClient

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
    """Scans for nearby BLE devices and returns a list."""
    try:
        # Scan for devices, timeout 5 seconds, and get advertisement data
        devices = await BleakScanner.discover(timeout=5.0, return_adv=True)
        device_list = []
        for d, adv in devices.values():
            device_list.append({
                "name": d.name or adv.local_name or "Unknown Device",
                "address": d.address,
                "rssi": adv.rssi,
            })
        
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
