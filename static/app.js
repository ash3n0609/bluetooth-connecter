document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const selectedFileInfo = document.getElementById('selected-file-info');
    const fileNameDisplay = document.getElementById('file-name-display');
    const fileSizeDisplay = document.getElementById('file-size-display');
    const clearFileBtn = document.getElementById('clear-file-btn');
    
    const scanBtn = document.getElementById('scan-btn');
    const btnText = scanBtn.querySelector('.btn-text');
    const btnSpinner = scanBtn.querySelector('.btn-spinner');
    const deviceTbody = document.getElementById('device-tbody');
    const statusMessage = document.getElementById('status-message');
    const deviceRowTemplate = document.getElementById('device-row-template');

    // State
    let selectedFile = null;
    let isScanning = false;

    // Event Listeners for File Selection
    dropZone.addEventListener('click', (e) => {
        if (e.target.closest('#clear-file-btn')) return;
        fileInput.click();
    });

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length) {
            handleFileSelection(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) {
            handleFileSelection(e.target.files[0]);
        }
    });

    clearFileBtn.addEventListener('click', () => {
        selectedFile = null;
        fileInput.value = '';
        selectedFileInfo.classList.add('hidden');
    });

    scanBtn.addEventListener('click', startScan);

    function formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const dm = 2;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }

    function handleFileSelection(file) {
        selectedFile = file;
        fileNameDisplay.textContent = file.name;
        fileSizeDisplay.textContent = formatBytes(file.size);
        selectedFileInfo.classList.remove('hidden');
    }

    function setStatus(message, type = 'info') {
        if (!message) {
            statusMessage.classList.add('hidden');
            return;
        }
        statusMessage.textContent = message;
        statusMessage.className = `status-${type}`;
        statusMessage.classList.remove('hidden');
        if (type === 'success' || type === 'error') {
            setTimeout(() => { statusMessage.classList.add('hidden'); }, 5000);
        }
    }

    async function startScan() {
        if (isScanning) return;
        
        isScanning = true;
        scanBtn.disabled = true;
        btnText.textContent = 'Scanning...';
        btnSpinner.classList.remove('hidden');
        
        try {
            const response = await fetch('/api/scan');
            const data = await response.json();
            
            if (data.status === 'success') {
                renderDevices(data.devices);
            } else {
                setStatus(`Scan error: ${data.message}`, 'error');
            }
        } catch (error) {
            setStatus('Failed to reach server for scanning.', 'error');
        } finally {
            isScanning = false;
            scanBtn.disabled = false;
            btnText.textContent = 'Discover Devices';
            btnSpinner.classList.add('hidden');
        }
    }

    function renderDevices(devices) {
        deviceTbody.innerHTML = '';
        
        if (devices.length === 0) {
            deviceTbody.innerHTML = '<tr class="empty-state"><td colspan="4">No Bluetooth devices found nearby.</td></tr>';
            return;
        }
        
        devices.forEach((device) => {
            const clone = deviceRowTemplate.content.cloneNode(true);
            const tr = clone.querySelector('tr');
            
            clone.querySelector('strong').textContent = device.name;
            clone.querySelector('.td-mac').textContent = device.address;
            
            const connectBtn = clone.querySelector('.connect-btn');
            const connectBleBtn = clone.querySelector('.connect-ble-btn');
            const sendBtn = clone.querySelector('.send-data-btn');
            const ipBadge = clone.querySelector('.td-ip .type-badge');
            
            if (device.type === 'Classic BT') {
                connectBleBtn.classList.add('hidden');
            }
            
            connectBleBtn.addEventListener('click', async () => {
                await connectBleDevice(device.address, connectBleBtn);
            });
            
            // Interaction logic per constraints: IP is unknown initially
            connectBtn.addEventListener('click', async () => {
                // Since Bluetooth cannot provide IP magically, we prompt user to identify it
                // If it's on the same subnet, they type it in, or we can use mDNS in the future.
                const ipInput = prompt(`Since Bluetooth cannot provide IP, enter the local IP address for ${device.name} (e.g. 192.168.1.15):`);
                if (!ipInput) return;
                
                await connectDevice(ipInput, connectBtn, sendBtn, ipBadge);
            });
            
            sendBtn.addEventListener('click', () => sendFile(sendBtn.dataset.ip));
            
            deviceTbody.appendChild(clone);
        });
    }

    async function connectBleDevice(mac, btn) {
        btn.disabled = true;
        btn.textContent = 'Receiving...';
        setStatus(`Attempting BLE connection and data reception from ${mac}...`, 'info');
        
        try {
            const response = await fetch(`/api/ble/connect/${encodeURIComponent(mac)}`, { method: 'POST' });
            const data = await response.json();
            
            if (data.status === 'success') {
                setStatus(`Successfully connected and received ${data.bytes_received || 0} bytes via BLE! Data saved locally.`, 'success');
            } else {
                setStatus(`BLE Error: ${data.message}`, 'error');
            }
        } catch (error) {
            setStatus('Network error during BLE connection', 'error');
        } finally {
            btn.disabled = false;
            btn.textContent = 'Connect BLE';
        }
    }

    async function connectDevice(ip, connectBtn, sendBtn, ipBadge) {
        connectBtn.disabled = true;
        connectBtn.textContent = 'Handshaking...';
        
        try {
            const response = await fetch(`/api/connect/${ip}`, { method: 'POST' });
            const data = await response.json();
            
            if (data.status === 'accepted') {
                setStatus(`Successfully connected via Wi-Fi to ${ip}`, 'success');
                ipBadge.textContent = ip;
                ipBadge.style.background = 'rgba(16, 185, 129, 0.2)';
                ipBadge.style.color = '#10b981';
                connectBtn.classList.add('hidden');
                
                sendBtn.dataset.ip = ip;
                sendBtn.classList.remove('hidden');
            } else {
                setStatus(`Wi-Fi Connection Error: ${data.message || 'Connection Refused'}`, 'error');
                connectBtn.textContent = 'Connect Wi-Fi';
            }
        } catch (error) {
            setStatus('Network error during Wi-Fi handshake', 'error');
            connectBtn.textContent = 'Connect Wi-Fi';
        } finally {
            connectBtn.disabled = false;
        }
    }

    async function sendFile(ip) {
        if (!selectedFile) {
            setStatus('Please select a file to send first!', 'error');
            return;
        }
        
        setStatus(`Attempting to send file to ${ip} via Wi-Fi...`, 'info');
        
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('ip', ip);
        
        try {
            const response = await fetch('/api/send', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            if (data.status === 'success') {
                setStatus(`File transferred securely over Wi-Fi! ${data.message}`, 'success');
            } else {
                setStatus(`Transfer error: ${data.message}`, 'error');
            }
        } catch (error) {
            setStatus('Network error during file transmission', 'error');
        }
    }
});
