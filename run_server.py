import os
import sys
import platform
import subprocess
import numpy as np
import time

DATA_FILE = "ecg_data_1758379673.npy"
WIN_TXT_FILE = "windows_ecg_data.txt"

def export_float_data():
    try:
        data = np.load(DATA_FILE)
        with open(WIN_TXT_FILE, "w") as f:
            for val in data:
                f.write(f"{val}\n")
    except Exception as e:
        print(f"Critcal Error reading numpy array: {e}")
        sys.exit(1)

def run_windows():
    print("Detected Windows OS. Triggering Native C# .NET BLE Core...")
    export_float_data()
    
    server_dir = os.path.join(os.path.dirname(__file__), "WindowsBLEServer")
    
    try:
        # Silently verify the Windows environment has the .NET compiler toolkit
        subprocess.run(["dotnet", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except Exception:
        print("ERROR: '.dotnet' execution engine not found on your Windows path.")
        print("To compile and run the native Windows BLE server, you must install the free Microsoft .NET 8.0 SDK.")
        print("Download it from: https://dotnet.microsoft.com/download")
        sys.exit(1)
        
    try:
        # Compile and run the background C# GATT Payload instantly
        subprocess.run(["dotnet", "run"], cwd=server_dir, check=True)
    except KeyboardInterrupt:
        print("\nWindows BLE Simulator Shutdown.")
    except Exception as e:
        print(f"Windows GATT Server Error: {e}")

def run_linux():
    print("Detected Linux OS. Launching standard `bless` DBus Server...")
    import asyncio
    try:
        from ble_sim import run_ble_server
    except ImportError:
        print("Error: ble_sim.py script not found in the current directory.")
        sys.exit(1)
        
    try:
        asyncio.run(run_ble_server())
    except KeyboardInterrupt:
        print("\nLinux BLE Simulator Shutdown.")

if __name__ == "__main__":
    current_os = platform.system()
    if current_os == 'Windows':
        run_windows()
    elif current_os == 'Linux':
        run_linux()
    else:
        print(f"OS '{current_os}' is not formally supported by this wrapper, falling back to Linux bless implementation...")
        run_linux()
