/**
 * DeviceBox - Frontend JavaScript
 * Apple-inspired Liquid Glass Interface
 */

class DeviceBoxApp {
    constructor() {
        this.refreshInterval = null;
        this.updateCheckInterval = null;
        this.isUpdating = false;
        this.autoUpdateEnabled = true;
        this.lastUpdateCheck = null;
        this.nextUpdateCheck = null;
        
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
        const refreshBtn = document.getElementById('refresh-btn');
        const autoUpdateToggle = document.getElementById('auto-update-toggle');
        
        if (checkUpdatesBtn) {
            checkUpdatesBtn.addEventListener('click', () => this.checkForUpdates());
        }
        
        if (updateBtn) {
            updateBtn.addEventListener('click', () => this.performUpdate());
        }
        
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshAll());
        }
        
        if (autoUpdateToggle) {
            autoUpdateToggle.addEventListener('change', (e) => {
                this.autoUpdateEnabled = e.target.checked;
                this.updateAutoUpdateStatus();
            });
        }
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'r') {
                e.preventDefault();
                this.refreshAll();
            }
        });
    }
    
    async loadInitialData() {
        try {
            await Promise.all([
                this.loadSystemStatus(),
                this.loadUpdateInfo(),
                this.loadSystemInfo()
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
            this.updateCPUStatus(data);
            this.updateMemoryStatus(data);
            this.updateStorageStatus(data);
            
        } catch (error) {
            this.showSystemStatusError(error.message);
        }
    }
    
    updateSystemStatus(data) {
        const container = document.getElementById('system-status');
        if (!container) return;
        
        const uptime = this.formatUptime(data.uptime);
        const temperature = data.temperature ? `${data.temperature.toFixed(1)}°C` : 'N/A';
        
        container.innerHTML = `
            <div class="status-item">
                <span class="status-label">Hostname</span>
                <span class="status-value">${data.hostname}</span>
            </div>
            <div class="status-item">
                <span class="status-label">Uptime</span>
                <span class="status-value">${uptime}</span>
            </div>
            <div class="status-item">
                <span class="status-label">Temperatur</span>
                <span class="status-value">${temperature}</span>
            </div>
            <div class="status-item">
                <span class="status-label">Status</span>
                <span class="status-value">
                    <span class="status-indicator online"></span>
                    Online
                </span>
            </div>
        `;
    }
    
    updateCPUStatus(data) {
        const container = document.getElementById('cpu-status');
        if (!container) return;
        
        const cpuPercent = data.cpu_percent.toFixed(1);
        const cpuModel = data.cpu_model || 'Raspberry Pi';
        
        container.innerHTML = `
            <div class="status-item">
                <span class="status-label">Modell</span>
                <span class="status-value">${cpuModel}</span>
            </div>
            <div class="status-item">
                <span class="status-label">Auslastung</span>
                <span class="status-value">${cpuPercent}%</span>
            </div>
            <div class="status-item">
                <span class="status-label">Status</span>
                <span class="status-value">
                    <span class="status-indicator ${this.getCpuStatusClass(cpuPercent)}"></span>
                    ${this.getCpuStatusText(cpuPercent)}
                </span>
            </div>
        `;
    }
    
    updateMemoryStatus(data) {
        const container = document.getElementById('memory-status');
        if (!container) return;
        
        const memoryPercent = data.memory_percent.toFixed(1);
        const memoryUsed = this.formatBytes(data.memory_used);
        const memoryTotal = this.formatBytes(data.memory_total);
        
        container.innerHTML = `
            <div class="status-item">
                <span class="status-label">Verwendet</span>
                <span class="status-value">${memoryUsed}</span>
            </div>
            <div class="status-item">
                <span class="status-label">Gesamt</span>
                <span class="status-value">${memoryTotal}</span>
            </div>
            <div class="status-item">
                <span class="status-label">Auslastung</span>
                <span class="status-value">${memoryPercent}%</span>
            </div>
            <div class="status-item">
                <span class="status-label">Status</span>
                <span class="status-value">
                    <span class="status-indicator ${this.getMemoryStatusClass(memoryPercent)}"></span>
                    ${this.getMemoryStatusText(memoryPercent)}
                </span>
            </div>
        `;
    }
    
    updateStorageStatus(data) {
        const container = document.getElementById('storage-status');
        if (!container) return;
        
        const diskPercent = data.disk_percent.toFixed(1);
        const diskUsed = this.formatBytes(data.disk_used);
        const diskTotal = this.formatBytes(data.disk_total);
        
        container.innerHTML = `
            <div class="status-item">
                <span class="status-label">Verwendet</span>
                <span class="status-value">${diskUsed}</span>
            </div>
            <div class="status-item">
                <span class="status-label">Gesamt</span>
                <span class="status-value">${diskTotal}</span>
            </div>
            <div class="status-item">
                <span class="status-label">Auslastung</span>
                <span class="status-value">${diskPercent}%</span>
            </div>
            <div class="status-item">
                <span class="status-label">Status</span>
                <span class="status-value">
                    <span class="status-indicator ${this.getStorageStatusClass(diskPercent)}"></span>
                    ${this.getStorageStatusText(diskPercent)}
                </span>
            </div>
        `;
    }
    
    showSystemStatusError(message) {
        const containers = [
            'system-status',
            'cpu-status', 
            'memory-status',
            'storage-status'
        ];
        
        containers.forEach(id => {
            const container = document.getElementById(id);
            if (container) {
                container.innerHTML = `
                    <div class="error-state">
                        <i class="fas fa-exclamation-triangle"></i>
                        <span>Fehler beim Laden: ${message}</span>
                    </div>
                `;
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
        const actionsContainer = document.getElementById('update-actions');
        const updateBtn = document.getElementById('update-btn');
        
        if (!container) return;
        
        if (data.available) {
            container.innerHTML = `
                <div class="update-available">
                    <i class="fas fa-download"></i>
                    <div class="update-details">
                        <h4>Update verfügbar!</h4>
                        <p>Aktuelle Version: <strong>${data.current_version}</strong></p>
                        <p>Neue Version: <strong>${data.latest_version}</strong></p>
                        ${data.release_notes ? `<p class="release-notes">${data.release_notes}</p>` : ''}
                    </div>
                </div>
            `;
            
            if (updateBtn) {
                updateBtn.style.display = 'inline-flex';
            }
        } else {
            container.innerHTML = `
                <div class="update-current">
                    <i class="fas fa-check-circle"></i>
                    <div class="update-details">
                        <h4>System ist aktuell</h4>
                        <p>Version: <strong>${data.current_version}</strong></p>
                        <p>Keine Updates verfügbar</p>
                    </div>
                </div>
            `;
            
            if (updateBtn) {
                updateBtn.style.display = 'none';
            }
        }
        
        if (actionsContainer) {
            actionsContainer.style.display = 'flex';
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
    
    async checkForUpdates(silent = false) {
        const btn = document.getElementById('check-updates-btn');
        if (btn && !silent) {
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Prüfe...';
        }
        
        try {
            await this.loadUpdateInfo();
            
            // Update last check time
            this.lastUpdateCheck = new Date();
            const lastCheckElement = document.getElementById('last-check');
            if (lastCheckElement) {
                lastCheckElement.textContent = this.formatTimestamp(this.lastUpdateCheck);
            }
            
            // Update next check time
            this.updateNextCheckTime();
            
            if (!silent) {
                this.showToast('Update-Check abgeschlossen', 'success');
            }
        } catch (error) {
            if (!silent) {
                this.showToast('Update-Check fehlgeschlagen', 'error');
            }
        } finally {
            if (btn && !silent) {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-search"></i> Jetzt prüfen';
            }
        }
    }
    
    async performUpdate() {
        if (this.isUpdating) {
            this.showToast('Update bereits in Bearbeitung', 'warning');
            return;
        }
        
        this.isUpdating = true;
        
        const updateBtn = document.getElementById('update-btn');
        const progressContainer = document.getElementById('update-progress');
        const actionsContainer = document.getElementById('update-actions');
        
        if (updateBtn) updateBtn.disabled = true;
        if (progressContainer) progressContainer.style.display = 'block';
        if (actionsContainer) actionsContainer.style.display = 'none';
        
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
            if (progressContainer) progressContainer.style.display = 'none';
            if (actionsContainer) actionsContainer.style.display = 'flex';
        }
    }
    
    async loadSystemInfo() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            this.updateSystemInfo(data);
            
        } catch (error) {
            this.showSystemInfoError(error.message);
        }
    }
    
    updateSystemInfo(data) {
        const container = document.getElementById('system-info');
        if (!container) return;
        
        container.innerHTML = `
            <div class="info-grid">
                <div class="info-item">
                    <span class="info-label">Betriebssystem</span>
                    <span class="info-value">${data.platform}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Hostname</span>
                    <span class="info-value">${data.hostname}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">CPU Modell</span>
                    <span class="info-value">${data.cpu_model}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Letzte Aktualisierung</span>
                    <span class="info-value">${this.formatTimestamp(data.timestamp)}</span>
                </div>
            </div>
        `;
    }
    
    showSystemInfoError(message) {
        const container = document.getElementById('system-info');
        if (!container) return;
        
        container.innerHTML = `
            <div class="error-state">
                <i class="fas fa-exclamation-triangle"></i>
                <span>Fehler beim Laden: ${message}</span>
            </div>
        `;
    }
    
    async refreshAll() {
        this.showToast('Daten werden aktualisiert...', 'info');
        await this.loadInitialData();
        this.showToast('Daten aktualisiert', 'success');
    }
    
    startAutoRefresh() {
        // Refresh every 30 seconds
        this.refreshInterval = setInterval(() => {
            this.loadSystemStatus();
        }, 30000);
        
        // Check for updates every 5 minutes if auto-update is enabled
        this.updateCheckInterval = setInterval(() => {
            if (this.autoUpdateEnabled) {
                this.checkForUpdates(true); // Silent check
            }
        }, 300000);
        
        // Update the next check time display
        this.updateNextCheckTime();
    }
    
    updateNextCheckTime() {
        const nextCheckElement = document.getElementById('next-check');
        if (nextCheckElement) {
            const now = new Date();
            const nextCheck = new Date(now.getTime() + 5 * 60 * 1000); // 5 minutes from now
            nextCheckElement.textContent = this.formatTimeUntil(nextCheck);
        }
    }
    
    updateAutoUpdateStatus() {
        if (this.autoUpdateEnabled) {
            this.startAutoRefresh();
            this.showToast('Automatische Updates aktiviert', 'success');
        } else {
            if (this.updateCheckInterval) {
                clearInterval(this.updateCheckInterval);
                this.updateCheckInterval = null;
            }
            this.showToast('Automatische Updates deaktiviert', 'info');
        }
    }
    
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        if (this.updateCheckInterval) {
            clearInterval(this.updateCheckInterval);
        }
    }
    
    // Utility Functions
    formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    formatUptime(seconds) {
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        
        if (days > 0) {
            return `${days}d ${hours}h ${minutes}m`;
        } else if (hours > 0) {
            return `${hours}h ${minutes}m`;
        } else {
            return `${minutes}m`;
        }
    }
    
    formatTimestamp(timestamp) {
        return new Date(timestamp).toLocaleString('de-DE');
    }
    
    formatTimeUntil(targetDate) {
        const now = new Date();
        const diff = targetDate.getTime() - now.getTime();
        
        if (diff <= 0) {
            return 'Jetzt';
        }
        
        const minutes = Math.floor(diff / (1000 * 60));
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);
        
        if (days > 0) {
            return `In ${days}d ${hours % 24}h`;
        } else if (hours > 0) {
            return `In ${hours}h ${minutes % 60}m`;
        } else {
            return `In ${minutes}m`;
        }
    }
    
    getCpuStatusClass(percent) {
        if (percent < 50) return 'online';
        if (percent < 80) return 'warning';
        return 'error';
    }
    
    getCpuStatusText(percent) {
        if (percent < 50) return 'Normal';
        if (percent < 80) return 'Hoch';
        return 'Kritisch';
    }
    
    getMemoryStatusClass(percent) {
        if (percent < 70) return 'online';
        if (percent < 90) return 'warning';
        return 'error';
    }
    
    getMemoryStatusText(percent) {
        if (percent < 70) return 'Normal';
        if (percent < 90) return 'Hoch';
        return 'Kritisch';
    }
    
    getStorageStatusClass(percent) {
        if (percent < 80) return 'online';
        if (percent < 95) return 'warning';
        return 'error';
    }
    
    getStorageStatusText(percent) {
        if (percent < 80) return 'Normal';
        if (percent < 95) return 'Hoch';
        return 'Kritisch';
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
    new DeviceBoxApp();
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
