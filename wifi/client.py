import httpx
import os

async def send_connection_request(ip: str):
    """Sends a POST request to establish a connection intention."""
    url = f"http://{ip}:8000/incoming"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url, json={"request": "connect"})
            return response.json()
    except Exception as e:
        return {"status": "error", "message": f"Failed to connect: {str(e)}"}

async def send_file_over_wifi(ip: str, file_path: str):
    """Sends a file securely over Wi-Fi HTTP."""
    url = f"http://{ip}:8000/upload"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            with open(file_path, "rb") as f:
                filename = os.path.basename(file_path)
                files = {'file': (filename, f)}
                response = await client.post(url, files=files)
            return response.json()
    except Exception as e:
        return {"status": "error", "message": f"File transfer failed: {str(e)}"}
