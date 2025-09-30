#!/bin/bash
# DeviceBox Update-Skript für curl-Ausführung
# Führt automatisch Updates ohne Benutzerinteraktion durch

set -e

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging-Funktionen
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Konfiguration
GITHUB_REPO="${GITHUB_REPO:-Musik-Wieland/DeviceBox}"
APP_NAME="${APP_NAME:-devicebox}"
INSTALL_DIR="${INSTALL_DIR:-/opt/devicebox}"
SERVICE_USER="${SERVICE_USER:-$(whoami)}"

log "DeviceBox Automatisches Update"
log "Repository: $GITHUB_REPO"
log "Installationsverzeichnis: $INSTALL_DIR"
log "Service User: $SERVICE_USER"

# Prüfe ob DeviceBox installiert ist
if [ ! -d "$INSTALL_DIR" ] || [ ! -f "$INSTALL_DIR/app.py" ]; then
    error "DeviceBox ist nicht installiert!"
    error "Führen Sie das Installationsskript aus:"
    error "curl -fsSL https://raw.githubusercontent.com/Musik-Wieland/DeviceBox/main/install.sh | bash"
    exit 1
fi

# Prüfe ob Auto-Update-Skript vorhanden ist
AUTO_UPDATE_SCRIPT="$INSTALL_DIR/auto_update.py"
if [ ! -f "$AUTO_UPDATE_SCRIPT" ]; then
    error "Auto-Update-Skript nicht gefunden: $AUTO_UPDATE_SCRIPT"
    exit 1
fi

log "Führe automatisches Update durch..."

# Stoppe den Service
log "Stoppe DeviceBox Service..."
sudo systemctl stop "$APP_NAME" 2>/dev/null || true

# Erstelle Backup
BACKUP_DIR="/opt/devicebox-backup-$(date +%Y%m%d-%H%M%S)"
log "Erstelle Backup in: $BACKUP_DIR"
sudo cp -r "$INSTALL_DIR" "$BACKUP_DIR"
sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$BACKUP_DIR"

# Führe Auto-Update aus
log "Führe Auto-Update aus..."
cd "$INSTALL_DIR"

# Aktiviere virtuelle Umgebung falls vorhanden
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Führe Auto-Update-Skript aus
if sudo -u "$SERVICE_USER" python3 "$AUTO_UPDATE_SCRIPT"; then
    success "Update erfolgreich abgeschlossen"
    
    # Starte den Service neu
    log "Starte DeviceBox Service neu..."
    sudo systemctl daemon-reload
    sudo systemctl enable "$APP_NAME"
    sudo systemctl start "$APP_NAME"
    
    # Prüfe Service-Status
    sleep 3
    if sudo systemctl is-active --quiet "$APP_NAME"; then
        success "DeviceBox Service läuft erfolgreich"
        
        # Lösche Backup nach erfolgreichem Update
        sudo rm -rf "$BACKUP_DIR"
        
        # Zeige IP-Adresse
        ip_address=$(hostname -I | awk '{print $1}')
        log "DeviceBox ist verfügbar unter:"
        log "  http://$ip_address"
        log "  http://$ip_address:8080"
        
    else
        error "DeviceBox Service konnte nicht gestartet werden"
        sudo systemctl status "$APP_NAME"
        exit 1
    fi
    
else
    error "Update fehlgeschlagen, verwende Backup..."
    sudo rm -rf "$INSTALL_DIR"
    sudo mv "$BACKUP_DIR" "$INSTALL_DIR"
    sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    sudo systemctl start "$APP_NAME"
    error "Update fehlgeschlagen, Installation auf vorherigen Stand zurückgesetzt"
    exit 1
fi

success "Automatisches Update abgeschlossen!"
log ""
log "Nützliche Befehle:"
log "  sudo systemctl status devicebox    # Service-Status"
log "  sudo systemctl restart devicebox    # Service neu starten"
log "  sudo journalctl -u devicebox -f     # Logs anzeigen"
