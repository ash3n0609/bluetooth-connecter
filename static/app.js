document.addEventListener('DOMContentLoaded', () => {
    const scanBtn = document.getElementById('scan-btn');
    const btnText = scanBtn.querySelector('.btn-text');
    const btnSpinner = scanBtn.querySelector('.btn-spinner');
    const statusMessage = document.getElementById('status-message');
    const deviceTbody = document.getElementById('device-tbody');

    // State
    let isScanning = false;
    let connectedDevices = new Set(); // Stores MAC addresses of connected devices

    scanBtn.addEventListener('click', startScan);

    function setStatus(message, type = 'info') {
        statusMessage.textContent = message;
        statusMessage.className = `status-message status-${type}`;
    }

    async function startScan() {
        if (isScanning) return;

        isScanning = true;
        scanBtn.disabled = true;
        btnText.textContent = 'Scanning...';
        btnSpinner.classList.remove('hidden');
        setStatus('Searching for nearby BLE devices...', 'info');

        try {
            const response = await fetch('/api/scan');
            const data = await response.json();

            if (data.status === 'success') {
                renderDevices(data.devices);
                setStatus(`Found ${data.devices.length} device(s)`, 'success');
            } else {
                setStatus(`Scan failed: ${data.message}`, 'error');
            }
        } catch (error) {
            setStatus('Failed to reach server. Is it running?', 'error');
            console.error(error);
        } finally {
            isScanning = false;
            scanBtn.disabled = false;
            btnText.textContent = 'Scan Devices';
            btnSpinner.classList.add('hidden');
        }
    }

    function getSignalColor(rssi) {
        if (rssi >= -60) return '#10b981'; // Green (Strong)
        if (rssi >= -80) return '#f59e0b'; // Yellow (Medium)
        return '#ef4444'; // Red (Weak)
    }

    function getSignalPercentage(rssi) {
        // Map RSSI (-100 to -40) to percentage (0 to 100)
        let percent = Math.min(Math.max(2 * (rssi + 100), 0), 100);
        return `${percent}%`;
    }

    function renderDevices(devices) {
        deviceTbody.innerHTML = '';

        if (devices.length === 0) {
            deviceTbody.innerHTML = `
                <tr class="empty-state">
                    <td colspan="4">No devices found. Try scanning again.</td>
                </tr>
            `;
            return;
        }

        let hasShownAvailableHeader = false;
        let hasShownPairedHeader = false;

        devices.forEach((device, index) => {
            if (!device.is_paired && !hasShownAvailableHeader) {
                const headerTr = document.createElement('tr');
                headerTr.className = 'section-header';
                headerTr.innerHTML = `<td colspan="4">Available Devices</td>`;
                deviceTbody.appendChild(headerTr);
                hasShownAvailableHeader = true;
            } else if (device.is_paired && !hasShownPairedHeader) {
                const headerTr = document.createElement('tr');
                headerTr.className = 'section-header';
                headerTr.innerHTML = `<td colspan="4">Paired Devices</td>`;
                deviceTbody.appendChild(headerTr);
                hasShownPairedHeader = true;
            }

            const tr = document.createElement('tr');
            tr.style.animation = `fadeIn 0.3s ease-out ${index * 0.05}s both`;

            const isConnected = connectedDevices.has(device.address);
            const btnClass = isConnected ? 'action-btn disconnect' : 'action-btn connect';
            const btnText = isConnected ? 'Disconnect' : 'Connect';

            tr.innerHTML = `
                <td>
                    <div class="device-name">
                        ${device.name}
                        ${device.is_paired ? '<span class="badge badge-paired">Paired</span>' : ''}
                    </div>
                </td>
                <td>
                    <div class="device-mac">${device.address}</div>
                </td>
                <td>
                    <div class="signal-strength">
                        <div class="signal-bar">
                            <div class="signal-fill" style="width: ${getSignalPercentage(device.rssi)}; background-color: ${getSignalColor(device.rssi)}"></div>
                        </div>
                        <span style="font-size: 0.85rem; color: var(--text-secondary)">${device.rssi} dBm</span>
                    </div>
                </td>
                <td>
                    <button class="${btnClass}" data-address="${device.address}">
                        ${btnText}
                    </button>
                </td>
            `;
            deviceTbody.appendChild(tr);
        });

        // Add event listeners to buttons
        const actionBtns = deviceTbody.querySelectorAll('.action-btn');
        actionBtns.forEach(btn => {
            btn.addEventListener('click', handleConnectionAction);
        });
    }

    async function handleConnectionAction(e) {
        const btn = e.target;
        const address = btn.dataset.address;
        const isConnect = btn.classList.contains('connect');

        btn.disabled = true;
        btn.textContent = isConnect ? 'Connecting...' : 'Disconnecting...';

        const endpoint = isConnect ? `/api/connect/${address}` : `/api/disconnect/${address}`;

        try {
            const response = await fetch(endpoint, { method: 'POST' });
            const data = await response.json();

            if (data.status === 'success') {
                setStatus(data.message, 'success');
                if (isConnect) {
                    connectedDevices.add(address);
                    btn.className = 'action-btn disconnect';
                    btn.textContent = 'Disconnect';
                } else {
                    connectedDevices.delete(address);
                    btn.className = 'action-btn connect';
                    btn.textContent = 'Connect';
                }
            } else {
                setStatus(`Failed: ${data.message}`, 'error');
                // Revert button state
                btn.textContent = isConnect ? 'Connect' : 'Disconnect';
            }
        } catch (error) {
            setStatus('Network error during connection', 'error');
            btn.textContent = isConnect ? 'Connect' : 'Disconnect';
        } finally {
            btn.disabled = false;
        }
    }
});
