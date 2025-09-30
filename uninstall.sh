#!/bin/bash
# DeviceBox Deinstallationsskript
# Entfernt alle DeviceBox-Komponenten und Abhängigkeiten vollständig

set -e  # Beende bei Fehlern

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging-Funktion
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

# Konfiguration aus Umgebungsvariablen oder Standardwerte
APP_NAME="${APP_NAME:-devicebox}"
INSTALL_DIR="${INSTALL_DIR:-/opt/devicebox}"
SERVICE_USER="${SERVICE_USER:-$(whoami)}"
PORT="${PORT:-8080}"

# Prüfe ob als Root ausgeführt
if [[ $EUID -eq 0 ]]; then
   error "Dieses Skript sollte nicht als Root ausgeführt werden!"
   error "Führe es als normaler Benutzer aus. Es wird sudo verwenden wenn nötig."
   exit 1
fi

# Prüfe ob sudo verfügbar ist
if ! command -v sudo &> /dev/null; then
    error "sudo ist nicht verfügbar. Bitte installiere es zuerst."
    exit 1
fi

log "DeviceBox Deinstallation gestartet..."
log "Installationsverzeichnis: $INSTALL_DIR"
log "Service User: $SERVICE_USER"
log "Port: $PORT"

# Bestätigung vom Benutzer
confirm_uninstall() {
    # Prüfe auf --force Flag
    if [[ "$1" == "--force" ]]; then
        warning "Force-Modus aktiviert - Deinstallation ohne Bestätigung"
        return 0
    fi
    
    warning "ACHTUNG: Dies wird DeviceBox vollständig deinstallieren!"
    warning "Alle Daten, Konfigurationen und Abhängigkeiten werden entfernt."
    echo ""
    warning "Folgende Komponenten werden entfernt:"
    echo "  - DeviceBox Service (systemd)"
    echo "  - Installationsverzeichnis: $INSTALL_DIR"
    echo "  - Nginx-Konfiguration"
    echo "  - Firewall-Regeln"
    echo "  - Python-Abhängigkeiten (optional)"
    echo ""
    echo "Verwendung:"
    echo "  ./uninstall.sh          # Interaktive Deinstallation"
    echo "  ./uninstall.sh --force  # Automatische Deinstallation"
    echo ""
    read -p "Möchten Sie fortfahren? (y/N): " -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        log "Deinstallation abgebrochen."
        exit 0
    fi
}

# Stoppe und entferne DeviceBox Service
remove_service() {
    log "Stoppe und entferne DeviceBox Service..."
    
    # Stoppe Service falls er läuft
    if sudo systemctl is-active --quiet devicebox 2>/dev/null; then
        log "Stoppe DeviceBox Service..."
        sudo systemctl stop devicebox
    fi
    
    # Deaktiviere Service
    if sudo systemctl is-enabled --quiet devicebox 2>/dev/null; then
        log "Deaktiviere DeviceBox Service..."
        sudo systemctl disable devicebox
    fi
    
    # Entferne Service-Datei
    if [ -f "/etc/systemd/system/devicebox.service" ]; then
        log "Entferne Service-Datei..."
        sudo rm -f /etc/systemd/system/devicebox.service
        sudo systemctl daemon-reload
        sudo systemctl reset-failed
    fi
    
    success "Service entfernt"
}

# Entferne Installationsverzeichnis
remove_installation() {
    log "Entferne Installationsverzeichnis..."
    
    if [ -d "$INSTALL_DIR" ]; then
        # Erstelle finales Backup vor Löschung
        backup_dir="/tmp/devicebox_final_backup_$(date +%Y%m%d_%H%M%S)"
        log "Erstelle finales Backup nach: $backup_dir"
        sudo cp -r "$INSTALL_DIR" "$backup_dir"
        sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$backup_dir"
        
        # Entferne Installationsverzeichnis
        sudo rm -rf "$INSTALL_DIR"
        success "Installationsverzeichnis entfernt"
        log "Finales Backup erstellt: $backup_dir"
    else
        warning "Installationsverzeichnis nicht gefunden: $INSTALL_DIR"
    fi
}

# Entferne Nginx-Konfiguration
remove_nginx_config() {
    log "Entferne Nginx-Konfiguration..."
    
    # Entferne DeviceBox-Site
    if [ -f "/etc/nginx/sites-available/devicebox" ]; then
        sudo rm -f /etc/nginx/sites-available/devicebox
        log "Nginx-Site-Konfiguration entfernt"
    fi
    
    # Entferne Symlink
    if [ -L "/etc/nginx/sites-enabled/devicebox" ]; then
        sudo rm -f /etc/nginx/sites-enabled/devicebox
        log "Nginx-Site-Symlink entfernt"
    fi
    
    # Stelle default-Site wieder her falls nötig
    if [ ! -L "/etc/nginx/sites-enabled/default" ] && [ -f "/etc/nginx/sites-available/default" ]; then
        sudo ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default
        log "Default Nginx-Site wiederhergestellt"
    fi
    
    # Teste Nginx-Konfiguration
    if sudo nginx -t 2>/dev/null; then
        sudo systemctl reload nginx
        success "Nginx-Konfiguration bereinigt"
    else
        warning "Nginx-Konfiguration hat Probleme, manuelle Überprüfung empfohlen"
    fi
}

# Entferne Firewall-Regeln
remove_firewall_rules() {
    log "Entferne Firewall-Regeln..."
    
    # Prüfe ob UFW aktiv ist
    if sudo ufw status | grep -q "Status: active"; then
        # Entferne DeviceBox-Port-Regel
        if sudo ufw status numbered | grep -q "$PORT"; then
            log "Entferne Firewall-Regel für Port $PORT..."
            sudo ufw delete allow "$PORT" 2>/dev/null || true
        fi
        
        success "Firewall-Regeln entfernt"
    else
        log "UFW nicht aktiv, keine Firewall-Regeln zu entfernen"
    fi
}

# Entferne Python-Abhängigkeiten (optional)
remove_python_dependencies() {
    log "Prüfe Python-Abhängigkeiten..."
    
    echo ""
    warning "Möchten Sie auch die Python-Abhängigkeiten entfernen?"
    warning "Dies kann andere Python-Projekte beeinträchtigen!"
    echo ""
    read -p "Python-Abhängigkeiten entfernen? (y/N): " -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        log "Entferne Python-Abhängigkeiten..."
        
        # Liste der DeviceBox-spezifischen Pakete
        packages=(
            "Flask"
            "Werkzeug" 
            "psutil"
            "requests"
            "python-dateutil"
            "python-dotenv"
            "colorlog"
            "cryptography"
        )
        
        for package in "${packages[@]}"; do
            if pip3 show "$package" &>/dev/null; then
                log "Entferne $package..."
                pip3 uninstall -y "$package" 2>/dev/null || true
            fi
        done
        
        success "Python-Abhängigkeiten entfernt"
    else
        log "Python-Abhängigkeiten beibehalten"
    fi
}

# Entferne System-Abhängigkeiten (optional)
remove_system_dependencies() {
    log "Prüfe System-Abhängigkeiten..."
    
    echo ""
    warning "Möchten Sie auch die System-Abhängigkeiten entfernen?"
    warning "Dies kann andere Anwendungen beeinträchtigen!"
    echo ""
    read -p "System-Abhängigkeiten entfernen? (y/N): " -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        log "Entferne System-Abhängigkeiten..."
        
        # Liste der installierten Pakete
        packages=(
            "nginx"
            "ufw"
            "git"
            "curl"
            "unzip"
            "python3-pip"
            "python3-venv"
        )
        
        for package in "${packages[@]}"; do
            if dpkg -l | grep -q "^ii  $package "; then
                log "Entferne $package..."
                sudo apt remove -y "$package" 2>/dev/null || true
            fi
        done
        
        # Autoremove für nicht mehr benötigte Pakete
        sudo apt autoremove -y
        
        success "System-Abhängigkeiten entfernt"
    else
        log "System-Abhängigkeiten beibehalten"
    fi
}

# Bereinige temporäre Dateien
cleanup_temp_files() {
    log "Bereinige temporäre Dateien..."
    
    # Entferne temporäre DeviceBox-Dateien
    sudo rm -rf /tmp/devicebox_* 2>/dev/null || true
    
    # Bereinige Logs
    sudo journalctl --vacuum-time=1d 2>/dev/null || true
    
    success "Temporäre Dateien bereinigt"
}

# Prüfe verbleibende Referenzen
check_remaining_references() {
    log "Prüfe verbleibende Referenzen..."
    
    # Suche nach DeviceBox-Referenzen in System-Dateien
    references_found=false
    
    # Prüfe crontab
    if crontab -l 2>/dev/null | grep -q "devicebox"; then
        warning "DeviceBox-Referenzen in crontab gefunden"
        references_found=true
    fi
    
    # Prüfe .bashrc/.profile
    if grep -q "devicebox" ~/.bashrc 2>/dev/null; then
        warning "DeviceBox-Referenzen in .bashrc gefunden"
        references_found=true
    fi
    
    if grep -q "devicebox" ~/.profile 2>/dev/null; then
        warning "DeviceBox-Referenzen in .profile gefunden"
        references_found=true
    fi
    
    # Prüfe laufende Prozesse
    if pgrep -f "devicebox" >/dev/null 2>&1; then
        warning "DeviceBox-Prozesse noch aktiv gefunden"
        references_found=true
    fi
    
    if [ "$references_found" = true ]; then
        warning "Einige Referenzen gefunden - manuelle Bereinigung empfohlen"
    else
        success "Keine verbleibenden Referenzen gefunden"
    fi
}

# Zeige Zusammenfassung
show_summary() {
    echo ""
    success "=== DeviceBox Deinstallation abgeschlossen! ==="
    echo ""
    log "Entfernte Komponenten:"
    log "  ✓ DeviceBox Service (systemd)"
    log "  ✓ Installationsverzeichnis: $INSTALL_DIR"
    log "  ✓ Nginx-Konfiguration"
    log "  ✓ Firewall-Regeln"
    echo ""
    log "Nützliche Befehle für Neuinstallation:"
    log "  curl -fsSL https://raw.githubusercontent.com/Musik-Wieland/DeviceBox/main/install.sh | bash"
    echo ""
    log "Bei Problemen:"
    log "  sudo systemctl status devicebox"
    log "  sudo journalctl -u devicebox"
    log "  sudo ufw status"
    echo ""
}

# Hauptdeinstallation
main() {
    log "=== DeviceBox Deinstallation ==="
    
    # Prüfe auf Force-Flag
    FORCE_MODE=false
    if [[ "$1" == "--force" ]]; then
        FORCE_MODE=true
    fi
    
    confirm_uninstall "$1"
    remove_service
    remove_installation
    remove_nginx_config
    remove_firewall_rules
    
    # Nur bei interaktiver Deinstallation nach Abhängigkeiten fragen
    if [[ "$FORCE_MODE" == false ]]; then
        remove_python_dependencies
        remove_system_dependencies
    else
        log "Force-Modus: Überspringe optionale Abhängigkeiten"
    fi
    
    cleanup_temp_files
    check_remaining_references
    show_summary
}

# Führe Deinstallation aus
main "$@"
