import socket

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connect to an external IP to force OS to resolve local interface IP
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

DEVICE_IDENTITY = {
    "name": socket.gethostname(),
    "device_type": "PC",
    "ip": get_local_ip(),
    "port": 8000
}
