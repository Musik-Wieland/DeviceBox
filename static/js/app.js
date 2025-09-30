/**
 * DeviceBox - Minimalistisches USB Manager Interface
 */

class DeviceBoxApp {
    constructor() {
        this.refreshInterval = null;
        this.isUpdating = false;
        this.currentDevice = null;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.loadInitialData();
        this.startAutoRefresh();
    }
    
    bindEvents() {
        // Update Button Events
        const checkUpdatesBtn = document.getElementById('check-updates-btn');
        const updateBtn = document.getElementById('update-btn');
        
        if (checkUpdatesBtn) {
            checkUpdatesBtn.addEventListener('click', () => this.checkForUpdates());
        }
        
        if (updateBtn) {
            updateBtn.addEventListener('click', () => this.performUpdate());
        }
        
        // Device Manager Events
        const refreshDevicesBtn = document.getElementById('refresh-devices-btn');
        if (refreshDevicesBtn) {
            refreshDevicesBtn.addEventListener('click', () => this.refreshDevices());
        }
        
        // Modal Events
        const closeConfigModal = document.getElementById('close-config-modal');
        const cancelConfig = document.getElementById('cancel-config');
        const saveConfig = document.getElementById('save-config');
        
        if (closeConfigModal) {
            closeConfigModal.addEventListener('click', () => this.closeConfigModal());
        }
        
        if (cancelConfig) {
            cancelConfig.addEventListener('click', () => this.closeConfigModal());
        }
        
        if (saveConfig) {
            saveConfig.addEventListener('click', () => this.saveDeviceConfig());
        }
        
        // Close modal on outside click
        const modal = document.getElementById('device-config-modal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeConfigModal();
                }
            });
        }
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeConfigModal();
            }
        });
    }
    
    async loadInitialData() {
        try {
            await Promise.all([
                this.loadSystemStatus(),
                this.loadUpdateInfo(),
                this.loadAvailableDevices(),
                this.loadConfiguredDevices()
            ]);
        } catch (error) {
            this.showToast('Fehler beim Laden der Daten', 'error');
            console.error('Error loading initial data:', error);
        }
    }
    
    async loadSystemStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            this.updateSystemStatus(data);
            
        } catch (error) {
            this.showSystemStatusError(error.message);
        }
    }
    
    updateSystemStatus(data) {
        // Update CPU
        const cpuElement = document.getElementById('cpu-percent');
        if (cpuElement) {
            cpuElement.textContent = `${data.cpu_percent.toFixed(1)}%`;
        }
        
        // Update Memory
        const memoryElement = document.getElementById('memory-percent');
        if (memoryElement) {
            memoryElement.textContent = `${data.memory_percent.toFixed(1)}%`;
        }
        
        // Update Storage
        const storageElement = document.getElementById('storage-percent');
        if (storageElement) {
            storageElement.textContent = `${data.disk_percent.toFixed(1)}%`;
        }
        
        // Update Temperature
        const tempElement = document.getElementById('temperature');
        if (tempElement) {
            tempElement.textContent = data.temperature ? `${data.temperature.toFixed(1)}°C` : 'N/A';
        }
    }
    
    showSystemStatusError(message) {
        const elements = ['cpu-percent', 'memory-percent', 'storage-percent', 'temperature'];
        elements.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = '--';
                element.title = `Fehler: ${message}`;
            }
        });
    }
    
    async loadUpdateInfo() {
        try {
            const response = await fetch('/api/check-updates');
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            this.updateUpdateInfo(data);
            
        } catch (error) {
            this.showUpdateError(error.message);
        }
    }
    
    updateUpdateInfo(data) {
        const container = document.getElementById('update-info');
        const updateBtn = document.getElementById('update-btn');
        
        if (!container) return;
        
        if (data.update_available) {
            container.innerHTML = `
                <div class="update-available">
                    <i class="fas fa-download"></i>
                    <div class="update-details">
                        <h4>Update verfügbar!</h4>
                        <p>Version ${data.current_version} → ${data.latest_version}</p>
                    </div>
                </div>
            `;
            
            if (updateBtn) {
                updateBtn.style.display = 'inline-flex';
            }
        } else {
            container.innerHTML = `
                <div class="update-status">
                    <i class="fas fa-check-circle"></i>
                    <span>System ist aktuell (v${data.current_version})</span>
                </div>
            `;
            
            if (updateBtn) {
                updateBtn.style.display = 'none';
            }
        }
    }
    
    showUpdateError(message) {
        const container = document.getElementById('update-info');
        if (!container) return;
        
        container.innerHTML = `
            <div class="update-error">
                <i class="fas fa-exclamation-triangle"></i>
                <div class="update-details">
                    <h4>Update-Check fehlgeschlagen</h4>
                    <p>${message}</p>
                </div>
            </div>
        `;
    }
    
    async performUpdate() {
        if (this.isUpdating) {
            this.showToast('Update bereits in Bearbeitung', 'warning');
            return;
        }
        
        this.isUpdating = true;
        
        const updateBtn = document.getElementById('update-btn');
        if (updateBtn) updateBtn.disabled = true;
        
        try {
            const response = await fetch('/api/update', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showToast('Update erfolgreich abgeschlossen!', 'success');
                setTimeout(() => {
                    window.location.reload();
                }, 2000);
            } else {
                throw new Error(data.error || 'Update fehlgeschlagen');
            }
            
        } catch (error) {
            this.showToast(`Update fehlgeschlagen: ${error.message}`, 'error');
        } finally {
            this.isUpdating = false;
            if (updateBtn) updateBtn.disabled = false;
        }
    }
    
    async loadAvailableDevices() {
        try {
            const response = await fetch('/api/devices/available');
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            this.updateAvailableDevices(data);
            
        } catch (error) {
            this.showAvailableDevicesError(error.message);
        }
    }
    
    updateAvailableDevices(devices) {
        const container = document.getElementById('available-devices');
        if (!container) return;
        
        if (devices.length === 0) {
            container.innerHTML = `
                <div class="loading-state">
                    <i class="fas fa-usb"></i>
                    <span>Keine USB-Geräte gefunden</span>
                </div>
            `;
            return;
        }
        
        container.innerHTML = devices.map(device => `
            <div class="device-item">
                <div class="device-info">
                    <div class="device-name">${device.description || 'Unbekanntes Gerät'}</div>
                    <div class="device-description">
                        ${device.type === 'usb' ? 
                            `USB: ${device.vendor_product}` : 
                            `Seriell: ${device.port}`
                        }
                        ${device.manufacturer ? ` - ${device.manufacturer}` : ''}
                    </div>
                </div>
                <div class="device-actions">
                    <button class="btn btn-primary btn-sm" onclick="deviceBoxApp.configureDevice('${JSON.stringify(device).replace(/'/g, "\\'")}')">
                        <i class="fas fa-cog"></i>
                        Einrichten
                    </button>
                </div>
            </div>
        `).join('');
    }
    
    showAvailableDevicesError(message) {
        const container = document.getElementById('available-devices');
        if (!container) return;
        
        container.innerHTML = `
            <div class="error-state">
                <i class="fas fa-exclamation-triangle"></i>
                <span>Fehler beim Laden: ${message}</span>
            </div>
        `;
    }
    
    async loadConfiguredDevices() {
        try {
            const response = await fetch('/api/devices');
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            this.updateConfiguredDevices(data);
            
        } catch (error) {
            this.showConfiguredDevicesError(error.message);
        }
    }
    
    updateConfiguredDevices(devices) {
        const container = document.getElementById('configured-devices');
        if (!container) return;
        
        const deviceList = Object.values(devices);
        
        if (deviceList.length === 0) {
            container.innerHTML = `
                <div class="loading-state">
                    <i class="fas fa-cog"></i>
                    <span>Keine konfigurierten Geräte</span>
                </div>
            `;
            return;
        }
        
        container.innerHTML = deviceList.map(device => `
            <div class="configured-device-card">
                <div class="device-header">
                    <div class="device-icon-small">
                        <i class="${this.getDeviceIcon(device.type)}"></i>
                    </div>
                    <div class="device-details">
                        <h5>${device.name}</h5>
                        <div class="device-model">${device.model}</div>
                    </div>
                </div>
                
                <div class="device-status">
                    <span class="status-indicator-small ${device.status}"></span>
                    <span>${this.getStatusText(device.status)}</span>
                </div>
                
                <div class="device-actions">
                    <button class="btn btn-success btn-sm" onclick="deviceBoxApp.connectDevice('${device.id}')">
                        <i class="fas fa-plug"></i>
                        Verbinden
                    </button>
                    <button class="btn btn-secondary btn-sm" onclick="deviceBoxApp.testDevice('${device.id}')">
                        <i class="fas fa-play"></i>
                        Testen
                    </button>
                    <button class="btn btn-danger btn-sm" onclick="deviceBoxApp.removeDevice('${device.id}')">
                        <i class="fas fa-trash"></i>
                        Entfernen
                    </button>
                </div>
            </div>
        `).join('');
    }
    
    showConfiguredDevicesError(message) {
        const container = document.getElementById('configured-devices');
        if (!container) return;
        
        container.innerHTML = `
            <div class="error-state">
                <i class="fas fa-exclamation-triangle"></i>
                <span>Fehler beim Laden: ${message}</span>
            </div>
        `;
    }
    
    configureDevice(deviceInfoStr) {
        try {
            const deviceInfo = JSON.parse(deviceInfoStr);
            this.currentDevice = deviceInfo;
            
            // Öffne Konfigurationsmodal
            const modal = document.getElementById('device-config-modal');
            if (modal) {
                modal.classList.add('show');
                
                // Setze Standardwerte
                const nameInput = document.getElementById('device-name');
                const typeSelect = document.getElementById('device-type');
                const modelInput = document.getElementById('device-model');
                
                if (nameInput) {
                    nameInput.value = deviceInfo.description || '';
                }
                
                if (modelInput) {
                    modelInput.value = deviceInfo.manufacturer || '';
                }
                
                // Fokus auf Name-Input
                if (nameInput) {
                    nameInput.focus();
                }
            }
            
        } catch (error) {
            this.showToast('Fehler beim Öffnen der Konfiguration', 'error');
            console.error('Error configuring device:', error);
        }
    }
    
    closeConfigModal() {
        const modal = document.getElementById('device-config-modal');
        if (modal) {
            modal.classList.remove('show');
            this.currentDevice = null;
        }
    }
    
    async saveDeviceConfig() {
        if (!this.currentDevice) {
            this.showToast('Kein Gerät ausgewählt', 'error');
            return;
        }
        
        const nameInput = document.getElementById('device-name');
        const typeSelect = document.getElementById('device-type');
        const modelInput = document.getElementById('device-model');
        
        if (!nameInput || !typeSelect || !modelInput) {
            this.showToast('Konfigurationsformular unvollständig', 'error');
            return;
        }
        
        const name = nameInput.value.trim();
        const type = typeSelect.value;
        const model = modelInput.value.trim();
        
        if (!name) {
            this.showToast('Bitte geben Sie einen Gerätenamen ein', 'warning');
            return;
        }
        
        try {
            const response = await fetch('/api/devices', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    device_type: type,
                    model: model,
                    device_info: this.currentDevice,
                    custom_name: name
                })
            });
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            this.showToast('Gerät erfolgreich konfiguriert', 'success');
            this.closeConfigModal();
            await this.loadConfiguredDevices();
            
        } catch (error) {
            this.showToast(`Fehler beim Speichern: ${error.message}`, 'error');
        }
    }
    
    async connectDevice(deviceId) {
        try {
            const response = await fetch(`/api/devices/${deviceId}/connect`, {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            this.showToast('Gerät erfolgreich verbunden', 'success');
            await this.loadConfiguredDevices();
            
        } catch (error) {
            this.showToast(`Fehler beim Verbinden: ${error.message}`, 'error');
        }
    }
    
    async testDevice(deviceId) {
        try {
            const response = await fetch(`/api/devices/${deviceId}/test`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    test_type: 'test_print'
                })
            });
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            this.showToast(data.message, data.success ? 'success' : 'error');
            
        } catch (error) {
            this.showToast(`Fehler beim Testen: ${error.message}`, 'error');
        }
    }
    
    async removeDevice(deviceId) {
        if (!confirm('Möchten Sie dieses Gerät wirklich entfernen?')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/devices/${deviceId}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            this.showToast('Gerät erfolgreich entfernt', 'success');
            await this.loadConfiguredDevices();
            
        } catch (error) {
            this.showToast(`Fehler beim Entfernen: ${error.message}`, 'error');
        }
    }
    
    async refreshDevices() {
        this.showToast('Geräte werden aktualisiert...', 'info');
        await Promise.all([
            this.loadAvailableDevices(),
            this.loadConfiguredDevices()
        ]);
        this.showToast('Geräte aktualisiert', 'success');
    }
    
    startAutoRefresh() {
        // Refresh system status every 30 seconds
        this.refreshInterval = setInterval(() => {
            this.loadSystemStatus();
        }, 30000);
    }
    
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
    }
    
    // Helper Functions
    getDeviceIcon(type) {
        const icons = {
            'printer': 'fas fa-print',
            'label_printer': 'fas fa-tag',
            'shipping_printer': 'fas fa-shipping-fast',
            'barcode_scanner': 'fas fa-barcode',
            'receipt_printer': 'fas fa-receipt',
            'card_reader': 'fas fa-credit-card'
        };
        return icons[type] || 'fas fa-usb';
    }
    
    getStatusText(status) {
        const statusTexts = {
            'connected': 'Verbunden',
            'disconnected': 'Getrennt',
            'error': 'Fehler'
        };
        return statusTexts[status] || 'Unbekannt';
    }
    
    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        if (!container) return;
        
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const iconMap = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };
        
        toast.innerHTML = `
            <i class="toast-icon ${iconMap[type]}"></i>
            <span class="toast-message">${message}</span>
            <button class="toast-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        container.appendChild(toast);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 5000);
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.deviceBoxApp = new DeviceBoxApp();
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // Page is hidden, stop auto-refresh
        if (window.deviceBoxApp) {
            window.deviceBoxApp.stopAutoRefresh();
        }
    } else {
        // Page is visible, restart auto-refresh
        if (window.deviceBoxApp) {
            window.deviceBoxApp.startAutoRefresh();
        }
    }
});
