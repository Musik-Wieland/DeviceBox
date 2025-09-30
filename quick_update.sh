#!/bin/bash
# DeviceBox Schnell-Update für bestehende Installationen
# Optimiert für curl-Ausführung ohne Benutzerinteraktion

set -e

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

# Konfiguration
INSTALL_DIR="/opt/devicebox"
SERVICE_USER="pi"

log "DeviceBox Schnell-Update"
log "Installationsverzeichnis: $INSTALL_DIR"

# Prüfe Installation
if [ ! -d "$INSTALL_DIR" ] || [ ! -f "$INSTALL_DIR/app.py" ]; then
    error "DeviceBox ist nicht installiert!"
    error "Führen Sie das Installationsskript aus:"
    error "curl -fsSL https://raw.githubusercontent.com/Musik-Wieland/DeviceBox/main/install.sh | bash"
    exit 1
fi

# Stoppe Service
log "Stoppe DeviceBox Service..."
sudo systemctl stop devicebox 2>/dev/null || true

# Backup erstellen
BACKUP_DIR="/opt/devicebox-backup-$(date +%Y%m%d-%H%M%S)"
log "Erstelle Backup: $BACKUP_DIR"
sudo cp -r "$INSTALL_DIR" "$BACKUP_DIR"
sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$BACKUP_DIR"

# Auto-Update ausführen
log "Führe Auto-Update aus..."
cd "$INSTALL_DIR"

if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

if sudo -u "$SERVICE_USER" python3 auto_update.py; then
    success "Update erfolgreich!"
    
    # Service neu starten
    log "Starte Service neu..."
    sudo systemctl daemon-reload
    sudo systemctl enable devicebox
    sudo systemctl start devicebox
    
    sleep 3
    if sudo systemctl is-active --quiet devicebox; then
        success "DeviceBox läuft erfolgreich!"
        
        # Backup löschen
        sudo rm -rf "$BACKUP_DIR"
        
        # IP anzeigen
        ip=$(hostname -I | awk '{print $1}')
        log "Verfügbar unter: http://$ip"
        
    else
        error "Service konnte nicht gestartet werden"
        sudo systemctl status devicebox
        exit 1
    fi
    
else
    error "Update fehlgeschlagen - stelle Backup wieder her..."
    sudo rm -rf "$INSTALL_DIR"
    sudo mv "$BACKUP_DIR" "$INSTALL_DIR"
    sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    sudo systemctl start devicebox
    error "Update fehlgeschlagen - Installation wiederhergestellt"
    exit 1
fi

success "Schnell-Update abgeschlossen!"
