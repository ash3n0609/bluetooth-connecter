from fastapi import APIRouter, UploadFile, File
import shutil
import os

router = APIRouter()
UPLOAD_DIR = "downloads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/incoming")
async def handle_incoming_connection(data: dict):
    """Handles an incoming request from another device."""
    print(f"Incoming request logged: {data}")
    return {"status": "accepted"}

@router.post("/upload")
async def handle_upload(file: UploadFile = File(...)):
    """Receives a file over Wi-Fi HTTP POST."""
    full_path = os.path.join(UPLOAD_DIR, file.filename)
    try:
        with open(full_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"status": "success", "message": f"File '{file.filename}' received and saved successfully."}
    except Exception as e:
        return {"status": "error", "message": str(e)}
