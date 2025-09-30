#!/bin/bash
# DeviceBox Fix-Update-Skript
# Behebt das Berechtigungsproblem beim Update

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

log "DeviceBox Fix-Update"
log "===================="

# Konfiguration
INSTALL_DIR="/opt/devicebox"
SERVICE_USER="pi"
GITHUB_REPO="Musik-Wieland/DeviceBox"

# Prüfe Installation
if [ ! -d "$INSTALL_DIR" ]; then
    error "DeviceBox ist nicht installiert!"
    exit 1
fi

# Stoppe Service
log "Stoppe DeviceBox Service..."
sudo systemctl stop devicebox 2>/dev/null || true

# Erstelle Backup
BACKUP_DIR="/opt/devicebox-backup-$(date +%Y%m%d-%H%M%S)"
log "Erstelle Backup: $BACKUP_DIR"
sudo cp -r "$INSTALL_DIR" "$BACKUP_DIR"
sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$BACKUP_DIR"

# Erstelle temporäres Verzeichnis
TEMP_DIR=$(mktemp -d)
log "Temporäres Verzeichnis: $TEMP_DIR"

# Lade Repository herunter
log "Lade Repository von GitHub herunter..."
cd "$TEMP_DIR"
curl -L "https://github.com/$GITHUB_REPO/archive/main.zip" -o repository.zip

# Extrahiere Repository
log "Extrahiere Repository..."
unzip -q repository.zip
EXTRACTED_DIR="$TEMP_DIR/DeviceBox-main"

# Erstelle temporäres Verzeichnis für alte Installation
OLD_INSTALL_DIR="/opt/devicebox_old"

# Entferne alte temporäre Installation falls vorhanden
sudo rm -rf "$OLD_INSTALL_DIR"

# Verschiebe aktuelle Installation
log "Verschiebe aktuelle Installation nach: $OLD_INSTALL_DIR"
sudo mv "$INSTALL_DIR" "$OLD_INSTALL_DIR"

# Kopiere neue Version
log "Kopiere neue Version nach: $INSTALL_DIR"
sudo cp -r "$EXTRACTED_DIR" "$INSTALL_DIR"

# Stelle wichtige Dateien wieder her
log "Stelle wichtige Dateien wieder her..."

# Datenverzeichnis
if [ -d "$OLD_INSTALL_DIR/data" ]; then
    sudo rm -rf "$INSTALL_DIR/data"
    sudo cp -r "$OLD_INSTALL_DIR/data" "$INSTALL_DIR/"
fi

# Virtuelle Umgebung
if [ -d "$OLD_INSTALL_DIR/venv" ]; then
    sudo rm -rf "$INSTALL_DIR/venv"
    sudo cp -r "$OLD_INSTALL_DIR/venv" "$INSTALL_DIR/"
fi

# Konfigurationsdateien
for config_file in config.json version.json; do
    if [ -f "$OLD_INSTALL_DIR/$config_file" ]; then
        sudo cp "$OLD_INSTALL_DIR/$config_file" "$INSTALL_DIR/"
    fi
done

# Setze Berechtigungen
log "Setze Berechtigungen für Benutzer: $SERVICE_USER"
sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"

# Setze ausführbare Berechtigungen
log "Setze ausführbare Berechtigungen..."
executable_files=(
    "app.py" "auto_update.py" "update.py" "update_simple.py"
    "device_manager.py" "debug_update.py" "test_update.py"
    "quick_update.sh" "update_curl.sh" "fix_update.py"
)

for file in "${executable_files[@]}"; do
    if [ -f "$INSTALL_DIR/$file" ]; then
        sudo chmod +x "$INSTALL_DIR/$file"
    fi
done

# Starte Service neu
log "Starte DeviceBox Service neu..."
sudo systemctl daemon-reload
sudo systemctl start devicebox

# Prüfe Service-Status
log "Prüfe Service-Status..."
sleep 3

if sudo systemctl is-active --quiet devicebox; then
    success "Service läuft erfolgreich!"
    
    # Entferne alte Installation
    log "Entferne alte Installation: $OLD_INSTALL_DIR"
    sudo rm -rf "$OLD_INSTALL_DIR"
    
    # Entferne Backup
    log "Entferne Backup: $BACKUP_DIR"
    sudo rm -rf "$BACKUP_DIR"
    
    # Entferne temporäres Verzeichnis
    rm -rf "$TEMP_DIR"
    
    success "Fix-Update erfolgreich abgeschlossen!"
    
    # Zeige IP-Adresse
    IP=$(hostname -I | awk '{print $1}')
    log "DeviceBox ist verfügbar unter: http://$IP"
    
else
    error "Service konnte nicht gestartet werden"
    
    # Rollback
    log "Führe Rollback durch..."
    sudo rm -rf "$INSTALL_DIR"
    sudo mv "$OLD_INSTALL_DIR" "$INSTALL_DIR"
    sudo systemctl start devicebox
    
    # Entferne temporäres Verzeichnis
    rm -rf "$TEMP_DIR"
    
    error "Rollback durchgeführt - alte Installation wiederhergestellt"
    exit 1
fi

log ""
log "Nützliche Befehle:"
log "  sudo systemctl status devicebox    # Service-Status"
log "  sudo systemctl restart devicebox    # Service neu starten"
log "  sudo journalctl -u devicebox -f     # Logs anzeigen"
