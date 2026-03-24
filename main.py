from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os
import shutil

# Modular imports
from core.identity import DEVICE_IDENTITY
from ble.scanner import scan_devices
from ble.connector import connect_and_receive_ble_data
from wifi.server import router as wifi_router
from wifi.client import send_connection_request, send_file_over_wifi

app = FastAPI(title="Hybrid Bluetooth/Wi-Fi Manager")

# Setup static folders
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Include the Wi-Fi receiving endpoints
app.include_router(wifi_router)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # Pass our identity directly to the template
    return templates.TemplateResponse(request=request, name="index.html", context={
        "request": request, 
        "identity": DEVICE_IDENTITY
    })

@app.get("/api/scan")
async def api_scan():
    """Triggers BLE scanning"""
    return await scan_devices()

@app.post("/api/connect/{ip}")
async def api_connect(ip: str):
    """Triggers an HTTP outgoing connection request to a specific IP."""
    return await send_connection_request(ip)

@app.post("/api/ble/connect/{mac}")
async def api_ble_connect(mac: str):
    """Triggers BLE connection to receive data"""
    return await connect_and_receive_ble_data(mac)

@app.post("/api/send")
async def api_send_file(ip: str = Form(...), file: UploadFile = File(...)):
    """Triggers an HTTP outgoing file transfer to a specific IP."""
    temp_path = f"temp_{file.filename}"
    try:
        # Save temp copy before pushing
        with open(temp_path, "wb") as buffer:
             shutil.copyfileobj(file.file, buffer)
        
        # Dispatch via wifi client
        result = await send_file_over_wifi(ip, temp_path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
    
    return result

@app.get("/api/downloads/{filename}")
async def download_file(filename: str):
    """Serves a saved .npy file from the downloads folder."""
    file_path = os.path.join("downloads", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(
        path=file_path,
        media_type="application/octet-stream",
        filename=filename
    )

@app.get("/api/downloads")
async def list_downloads():
    """Lists all saved .npy files in the downloads folder."""
    os.makedirs("downloads", exist_ok=True)
    files = [
        {"filename": f, "size_bytes": os.path.getsize(os.path.join("downloads", f))}
        for f in os.listdir("downloads")
        if f.endswith(".npy")
    ]
    return {"status": "success", "files": sorted(files, key=lambda x: x["filename"], reverse=True)}

if __name__ == "__main__":
    import uvicorn
    # uvicorn main:app --host 0.0.0.0 --port 8000
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
