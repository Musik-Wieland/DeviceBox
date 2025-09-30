#!/bin/bash

# DeviceBox - Automatisches Deinstallationsskript
# Einzeiler: curl -sSL https://raw.githubusercontent.com/Musik-Wieland/DeviceBox/main/uninstall.sh | bash

set -e

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging Funktionen
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Banner
print_banner() {
    echo -e "${RED}"
    echo "    ____            _           ____            "
    echo "   / __ \___ _   __(_)_______  / __ )____  _  __"
    echo "  / / / / _ \ | / / / ___/ _ \/ __  / __ \| |/_/"
    echo " / /_/ /  __/ |/ / / /__/  __/ /_/ / /_/ />  <  "
    echo "/_____/\___/|___/_/\___/\___/_____/\____/_/|_|  "
    echo "                                                "
    echo -e "${NC}"
    echo "DeviceBox Automatische Deinstallation"
    echo "====================================="
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "Führen Sie dieses Script nicht als root aus"
        exit 1
    fi
}

# Stop and remove service
remove_service() {
    log "Stoppe DeviceBox Service..."
    
    # Stop service
    sudo systemctl stop devicebox 2>/dev/null || true
    
    # Disable service
    sudo systemctl disable devicebox 2>/dev/null || true
    
    # Remove service file
    sudo rm -f /etc/systemd/system/devicebox.service
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    log "Service entfernt"
}

# Remove installation directory
remove_installation() {
    log "Entferne DeviceBox Installation..."
    
    INSTALL_DIR="/home/$USER/devicebox"
    
    if [[ -d "$INSTALL_DIR" ]]; then
        rm -rf "$INSTALL_DIR"
        log "Installationsverzeichnis entfernt: $INSTALL_DIR"
    else
        warning "Installationsverzeichnis nicht gefunden: $INSTALL_DIR"
    fi
}

# Remove firewall rules
remove_firewall() {
    log "Entferne Firewall-Regeln..."
    
    if command -v ufw &> /dev/null; then
        sudo ufw delete allow 5000/tcp 2>/dev/null || true
        log "Firewall-Regeln entfernt"
    else
        warning "UFW nicht installiert, überspringe Firewall-Bereinigung"
    fi
}

# Main deinstallation
main() {
    print_banner
    
    info "DeviceBox Automatische Deinstallation für Benutzer: $USER"
    warning "DeviceBox wird jetzt vollständig von Ihrem System entfernt..."
    
    # Deinstallation steps - KEINE RÜCKFRAGE!
    check_root
    remove_service
    remove_installation
    remove_firewall
    
    # Success message
    echo
    log "Deinstallation erfolgreich abgeschlossen!"
    echo
    echo -e "${GREEN}DeviceBox wurde vollständig von Ihrem System entfernt.${NC}"
    echo -e "${YELLOW}Sie können es jederzeit mit dem Installationsskript neu installieren.${NC}"
}

# Run main function
main "$@"
