// DeviceBox - Frontend JavaScript
class DeviceBoxApp {
    constructor() {
        this.apiBase = '/api';
        this.updateInterval = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadInitialData();
        this.startStatusUpdates();
    }

    setupEventListeners() {
        // Update buttons
        document.getElementById('checkUpdatesBtn').addEventListener('click', () => this.checkForUpdates());
        document.getElementById('updateBtn').addEventListener('click', () => this.performUpdate());
        
        // Action buttons
        document.getElementById('rebootBtn').addEventListener('click', () => this.rebootSystem());
        document.getElementById('refreshStatusBtn').addEventListener('click', () => this.refreshStatus());
    }

    async loadInitialData() {
        try {
            await Promise.all([
                this.loadVersionInfo(),
                this.loadDeviceStatus()
            ]);
        } catch (error) {
            this.showToast('Fehler beim Laden der Daten', 'error');
            console.error('Initial data load error:', error);
        }
    }

    async loadVersionInfo() {
        try {
            const response = await fetch(`${this.apiBase}/version`);
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            document.getElementById('currentVersion').textContent = data.version;
            document.getElementById('currentVersionInfo').textContent = data.version;
        } catch (error) {
            document.getElementById('currentVersion').textContent = 'Fehler';
            document.getElementById('currentVersionInfo').textContent = 'Fehler';
            console.error('Version load error:', error);
        }
    }

    async loadDeviceStatus() {
        try {
            const response = await fetch(`${this.apiBase}/status`);
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            this.updateStatusDisplay(data);
        } catch (error) {
            this.showToast('Fehler beim Laden des Gerätestatus', 'error');
            console.error('Status load error:', error);
        }
    }

    updateStatusDisplay(data) {
        // CPU
        if (data.cpu && !data.cpu.error) {
            document.getElementById('cpuUsage').textContent = `${data.cpu.usage_percent.toFixed(1)}%`;
            if (data.temperature && !data.temperature.error) {
                document.getElementById('cpuTemp').textContent = `${data.temperature.cpu_temp.toFixed(1)}°C`;
            }
        }

        // Memory
        if (data.memory && !data.memory.error) {
            document.getElementById('memoryUsage').textContent = `${data.memory.usage_percent.toFixed(1)}%`;
            document.getElementById('memoryAvailable').textContent = `${(data.memory.available / 1024 / 1024 / 1024).toFixed(1)} GB`;
        }

        // Disk
        if (data.disk && !data.disk.error) {
            document.getElementById('diskUsage').textContent = `${data.disk.usage_percent.toFixed(1)}%`;
            document.getElementById('diskAvailable').textContent = `${(data.disk.free / 1024 / 1024 / 1024).toFixed(1)} GB`;
        }

        // Network
        if (data.network && !data.network.error) {
            document.getElementById('networkConnections').textContent = data.network.connections;
        }

        // Uptime
        if (data.uptime && !data.uptime.error) {
            const days = data.uptime.uptime_days;
            const hours = data.uptime.uptime_hours;
            const minutes = data.uptime.uptime_minutes;
            
            let uptimeText = '';
            if (days > 0) uptimeText += `${days}d `;
            if (hours > 0) uptimeText += `${hours}h `;
            uptimeText += `${minutes}m`;
            
            document.getElementById('systemUptime').textContent = uptimeText;
        }
    }

    async checkForUpdates() {
        const checkBtn = document.getElementById('checkUpdatesBtn');
        const updateBtn = document.getElementById('updateBtn');
        const latestVersionEl = document.getElementById('latestVersionInfo');
        
        try {
            checkBtn.disabled = true;
            checkBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Prüfen...';
            
            const response = await fetch(`${this.apiBase}/check-updates`);
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            latestVersionEl.textContent = data.latest_version;
            
            if (data.update_available) {
                updateBtn.disabled = false;
                this.showToast(`Update verfügbar: ${data.latest_version}`, 'success');
            } else {
                updateBtn.disabled = true;
                this.showToast('System ist auf dem neuesten Stand', 'info');
            }
            
        } catch (error) {
            latestVersionEl.textContent = 'Fehler';
            this.showToast('Fehler beim Prüfen auf Updates', 'error');
            console.error('Update check error:', error);
        } finally {
            checkBtn.disabled = false;
            checkBtn.innerHTML = '<i class="fas fa-search"></i> Nach Updates suchen';
        }
    }

    async performUpdate() {
        const updateBtn = document.getElementById('updateBtn');
        const updateLog = document.getElementById('updateLog');
        const logContent = document.getElementById('logContent');
        
        if (!confirm('Möchten Sie das Update wirklich installieren? Das System wird während des Updates kurzzeitig nicht verfügbar sein.')) {
            return;
        }
        
        try {
            updateBtn.disabled = true;
            updateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Update läuft...';
            updateLog.style.display = 'block';
            logContent.textContent = 'Update wird gestartet...\n';
            
            const response = await fetch(`${this.apiBase}/update`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            logContent.textContent += `\n${data.message}\n`;
            
            if (data.status === 'success') {
                this.showToast('Update erfolgreich installiert!', 'success');
                setTimeout(() => {
                    window.location.reload();
                }, 2000);
            } else if (data.status === 'no_update') {
                this.showToast('Kein Update verfügbar', 'info');
            }
            
        } catch (error) {
            logContent.textContent += `\nFehler: ${error.message}\n`;
            this.showToast('Fehler beim Update', 'error');
            console.error('Update error:', error);
        } finally {
            updateBtn.disabled = false;
            updateBtn.innerHTML = '<i class="fas fa-download"></i> Update installieren';
        }
    }

    async rebootSystem() {
        if (!confirm('Möchten Sie das System wirklich neu starten?')) {
            return;
        }
        
        try {
            const response = await fetch(`${this.apiBase}/reboot`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            this.showToast('System wird neu gestartet...', 'warning');
            
            // Countdown
            let countdown = 10;
            const countdownInterval = setInterval(() => {
                this.showToast(`System startet neu in ${countdown} Sekunden...`, 'warning');
                countdown--;
                
                if (countdown <= 0) {
                    clearInterval(countdownInterval);
                    this.showToast('System wird neu gestartet...', 'warning');
                }
            }, 1000);
            
        } catch (error) {
            this.showToast('Fehler beim Neustart', 'error');
            console.error('Reboot error:', error);
        }
    }

    async refreshStatus() {
        const refreshBtn = document.getElementById('refreshStatusBtn');
        
        try {
            refreshBtn.disabled = true;
            refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Aktualisieren...';
            
            await this.loadDeviceStatus();
            this.showToast('Status aktualisiert', 'success');
            
        } catch (error) {
            this.showToast('Fehler beim Aktualisieren', 'error');
            console.error('Refresh error:', error);
        } finally {
            refreshBtn.disabled = false;
            refreshBtn.innerHTML = '<i class="fas fa-refresh"></i> Status aktualisieren';
        }
    }

    startStatusUpdates() {
        // Update status every 30 seconds
        this.updateInterval = setInterval(() => {
            this.loadDeviceStatus();
        }, 30000);
    }

    showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        
        toastContainer.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 5000);
    }

    showLoading() {
        document.getElementById('loadingOverlay').classList.remove('hidden');
    }

    hideLoading() {
        document.getElementById('loadingOverlay').classList.add('hidden');
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new DeviceBoxApp();
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // Page is hidden, could pause updates
    } else {
        // Page is visible, resume updates
        window.location.reload();
    }
});
