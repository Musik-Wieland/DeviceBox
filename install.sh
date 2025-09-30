#!/bin/bash

# DeviceBox Installation Script für Raspberry Pi
# Einzeiler Installation: curl -sSL https://raw.githubusercontent.com/Musik-Wieland/DeviceBox/main/install.sh | bash

set -e

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging Funktion
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
    echo -e "${BLUE}"
    echo "    ____            _           ____            "
    echo "   / __ \___ _   __(_)_______  / __ )____  _  __"
    echo "  / / / / _ \ | / / / ___/ _ \/ __  / __ \| |/_/"
    echo " / /_/ /  __/ |/ / / /__/  __/ /_/ / /_/ />  <  "
    echo "/_____/\___/|___/_/\___/\___/_____/\____/_/|_|  "
    echo "                                                "
    echo -e "${NC}"
    echo "Raspberry Pi Web Interface Installation"
    echo "========================================"
}

# System Check
check_system() {
    log "Überprüfe System..."
    
    # Check if running on Raspberry Pi
    if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        warning "Dieses Script ist für Raspberry Pi optimiert"
    fi
    
    # Check OS
    if [[ ! -f /etc/os-release ]]; then
        error "Unbekanntes Betriebssystem"
        exit 1
    fi
    
    source /etc/os-release
    if [[ "$ID" != "raspbian" && "$ID" != "debian" ]]; then
        warning "Ungetestetes Betriebssystem: $ID"
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        error "Python3 ist nicht installiert"
        exit 1
    fi
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        log "Installiere pip3..."
        sudo apt update
        sudo apt install -y python3-pip
    fi
    
    log "System-Check erfolgreich"
}

# Update System
update_system() {
    log "Aktualisiere System-Pakete..."
    sudo apt update
    sudo apt upgrade -y
    sudo apt install -y git curl wget python3-venv python3-dev build-essential
    log "System aktualisiert"
}

# Install DeviceBox
install_devicebox() {
    log "Installiere DeviceBox..."
    
    # Create directory
    INSTALL_DIR="/home/pi/devicebox"
    if [[ -d "$INSTALL_DIR" ]]; then
        warning "DeviceBox ist bereits installiert"
        read -p "Möchten Sie eine Neuinstallation durchführen? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log "Entferne alte Installation..."
            sudo systemctl stop devicebox 2>/dev/null || true
            sudo systemctl disable devicebox 2>/dev/null || true
            rm -rf "$INSTALL_DIR"
        else
            log "Installation abgebrochen"
            exit 0
        fi
    fi
    
    # Create installation directory
    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    
    # Clone repository (fallback to local files if not available)
    if command -v git &> /dev/null; then
        log "Klone Repository..."
        
        # Check for GitHub token for private repositories
        if [[ -n "$GITHUB_TOKEN" ]]; then
            log "Verwende GitHub Token für privates Repository..."
            git clone https://${GITHUB_TOKEN}@github.com/Musik-Wieland/DeviceBox.git . || {
                warning "Repository nicht verfügbar, verwende lokale Dateien..."
                # Copy local files if git clone fails
                cp -r /tmp/devicebox/* . 2>/dev/null || {
                    error "Keine lokalen Dateien gefunden"
                    exit 1
                }
            }
        else
            git clone https://github.com/Musik-Wieland/DeviceBox.git . || {
                warning "Repository nicht verfügbar, verwende lokale Dateien..."
                # Copy local files if git clone fails
                cp -r /tmp/devicebox/* . 2>/dev/null || {
                    error "Keine lokalen Dateien gefunden"
                    exit 1
                }
            }
        fi
    else
        error "Git ist nicht installiert"
        exit 1
    fi
    
    # Create virtual environment
    log "Erstelle virtuelle Umgebung..."
    python3 -m venv venv
    source venv/bin/activate
    
    # Install Python dependencies
    log "Installiere Python-Abhängigkeiten..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Create version file
    log "Erstelle Versionsdatei..."
    cat > version.json << EOF
{
  "version": "1.0.0",
  "build_date": "$(date -Iseconds)",
  "commit_hash": "initial"
}
EOF
    
    # Set permissions
    chown -R pi:pi "$INSTALL_DIR"
    chmod +x app.py
    
    log "DeviceBox installiert"
}

# Setup systemd service
setup_service() {
    log "Richte Systemd-Service ein..."
    
    # Copy service file
    sudo cp devicebox.service /etc/systemd/system/
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    # Enable service
    sudo systemctl enable devicebox
    
    # Start service
    sudo systemctl start devicebox
    
    # Check status
    if sudo systemctl is-active --quiet devicebox; then
        log "DeviceBox Service läuft erfolgreich"
    else
        error "DeviceBox Service konnte nicht gestartet werden"
        sudo systemctl status devicebox
        exit 1
    fi
}

# Setup firewall
setup_firewall() {
    log "Richte Firewall ein..."
    
    # Install ufw if not present
    if ! command -v ufw &> /dev/null; then
        sudo apt install -y ufw
    fi
    
    # Configure firewall
    sudo ufw --force enable
    sudo ufw allow ssh
    sudo ufw allow 5000/tcp comment "DeviceBox Web Interface"
    
    log "Firewall konfiguriert"
}

# Get IP address
get_ip_address() {
    log "Ermittle IP-Adresse..."
    
    # Try different methods to get IP
    IP_ADDRESS=""
    
    # Method 1: hostname -I
    if command -v hostname &> /dev/null; then
        IP_ADDRESS=$(hostname -I | awk '{print $1}')
    fi
    
    # Method 2: ip command
    if [[ -z "$IP_ADDRESS" ]] && command -v ip &> /dev/null; then
        IP_ADDRESS=$(ip route get 1.1.1.1 | awk '{print $7; exit}')
    fi
    
    # Method 3: ifconfig
    if [[ -z "$IP_ADDRESS" ]] && command -v ifconfig &> /dev/null; then
        IP_ADDRESS=$(ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1' | head -1)
    fi
    
    echo "$IP_ADDRESS"
}

# Main installation
main() {
    print_banner
    
    # Check if running as root
    if [[ $EUID -eq 0 ]]; then
        error "Führen Sie dieses Script nicht als root aus"
        exit 1
    fi
    
    # Check if user is pi
    if [[ "$USER" != "pi" ]]; then
        warning "Dieses Script ist für den Benutzer 'pi' optimiert"
        read -p "Möchten Sie fortfahren? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 0
        fi
    fi
    
    # Installation steps
    check_system
    update_system
    install_devicebox
    setup_service
    setup_firewall
    
    # Get IP address
    IP_ADDRESS=$(get_ip_address)
    
    # Success message
    echo
    log "Installation erfolgreich abgeschlossen!"
    echo
    echo -e "${GREEN}DeviceBox ist jetzt verfügbar unter:${NC}"
    echo -e "${BLUE}  http://$IP_ADDRESS:5000${NC}"
    echo
    echo -e "${YELLOW}Service-Befehle:${NC}"
    echo -e "  Status anzeigen: ${BLUE}sudo systemctl status devicebox${NC}"
    echo -e "  Neustart:        ${BLUE}sudo systemctl restart devicebox${NC}"
    echo -e "  Stoppen:         ${BLUE}sudo systemctl stop devicebox${NC}"
    echo -e "  Logs anzeigen:   ${BLUE}sudo journalctl -u devicebox -f${NC}"
    echo
    echo -e "${GREEN}DeviceBox startet automatisch nach jedem Neustart!${NC}"
}

# Run main function
main "$@"
