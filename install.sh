#!/bin/bash
# DeviceBox Installationsskript für Raspberry Pi
# Universell und dynamisch - keine Hardcodierung

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
GITHUB_REPO="${GITHUB_REPO:-Musik-Wieland/DeviceBox}"
APP_NAME="${APP_NAME:-devicebox}"
INSTALL_DIR="${INSTALL_DIR:-/opt/devicebox}"
SERVICE_USER="${SERVICE_USER:-$(whoami)}"
PORT="${PORT:-8080}"
HOST="${HOST:-0.0.0.0}"

# Prüfe ob DeviceBox bereits installiert ist
EXISTING_INSTALLATION=false
if [ -d "$INSTALL_DIR" ] && [ -f "$INSTALL_DIR/app.py" ]; then
    EXISTING_INSTALLATION=true
fi

# Prüfe auf Flags
FORCE_UPDATE=false
SHOW_HELP=false

for arg in "$@"; do
    case $arg in
        --force-update)
            FORCE_UPDATE=true
            ;;
        --help|-h)
            SHOW_HELP=true
            ;;
    esac
done

# Zeige Hilfe
if [ "$SHOW_HELP" = true ]; then
    echo "DeviceBox Installationsskript"
    echo ""
    echo "Verwendung:"
    echo "  $0                    # Normale Installation/Update"
    echo "  $0 --force-update     # Automatisches Update ohne Nachfrage"
    echo "  $0 --help             # Diese Hilfe anzeigen"
    echo ""
    echo "Umgebungsvariablen:"
    echo "  GITHUB_REPO           # GitHub Repository (Standard: Musik-Wieland/DeviceBox)"
    echo "  APP_NAME              # Anwendungsname (Standard: devicebox)"
    echo "  INSTALL_DIR           # Installationsverzeichnis (Standard: /opt/devicebox)"
    echo "  SERVICE_USER          # Service-Benutzer (Standard: aktueller Benutzer)"
    echo "  PORT                  # Port (Standard: 8080)"
    echo "  HOST                  # Host (Standard: 0.0.0.0)"
    echo ""
    echo "Beispiele:"
    echo "  curl -fsSL https://raw.githubusercontent.com/Musik-Wieland/DeviceBox/main/install.sh | bash"
    echo "  curl -fsSL https://raw.githubusercontent.com/Musik-Wieland/DeviceBox/main/install.sh | bash -s -- --force-update"
    exit 0
fi

# Debug: Zeige aktuelle Konfiguration
log "Aktuelle Konfiguration:"
log "  SERVICE_USER: $SERVICE_USER"
log "  INSTALL_DIR: $INSTALL_DIR"
log "  GITHUB_REPO: $GITHUB_REPO"
log "  Bestehende Installation: $EXISTING_INSTALLATION"
log "  Force-Update: $FORCE_UPDATE"

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

log "DeviceBox Installation gestartet..."
log "Repository: $GITHUB_REPO"
log "App Name: $APP_NAME"
log "Installationsverzeichnis: $INSTALL_DIR"
log "Service User: $SERVICE_USER"
log "Port: $PORT"

# Prüfe System-Anforderungen
check_system() {
    log "Prüfe System-Anforderungen..."
    
    # Prüfe ob es ein Raspberry Pi ist
    if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        warning "Dieses System scheint kein Raspberry Pi zu sein. Fortfahren? (y/N)"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            log "Installation abgebrochen."
            exit 1
        fi
    fi
    
    # Prüfe verfügbaren Speicherplatz
    available_space=$(df / | awk 'NR==2 {print $4}')
    if [ "$available_space" -lt 1048576 ]; then  # 1GB in KB
        error "Nicht genügend Speicherplatz verfügbar (mindestens 1GB erforderlich)"
        exit 1
    fi
    
    # Prüfe Python 3
    if ! command -v python3 &> /dev/null; then
        error "Python 3 ist nicht installiert!"
        exit 1
    fi
    
    # Prüfe pip
    if ! command -v pip3 &> /dev/null; then
        log "pip3 nicht gefunden, installiere es..."
        sudo apt update
        sudo apt install -y python3-pip
    fi
    
    success "System-Anforderungen erfüllt"
}

# Update-Funktion für bestehende Installationen
perform_update() {
    log "Führe Update für bestehende Installation durch..."
    
    # Stoppe den Service
    log "Stoppe DeviceBox Service..."
    sudo systemctl stop "$APP_NAME" 2>/dev/null || true
    
    # Erstelle Backup der aktuellen Installation
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
    if [ -f "auto_update.py" ]; then
        sudo -u "$SERVICE_USER" python3 auto_update.py
        UPDATE_SUCCESS=$?
        
        if [ $UPDATE_SUCCESS -eq 0 ]; then
            success "Update erfolgreich abgeschlossen"
        else
            warning "Update fehlgeschlagen, verwende Backup..."
            sudo rm -rf "$INSTALL_DIR"
            sudo mv "$BACKUP_DIR" "$INSTALL_DIR"
            sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
            error "Update fehlgeschlagen, Installation auf vorherigen Stand zurückgesetzt"
            return 1
        fi
    else
        error "Auto-Update-Skript nicht gefunden"
        return 1
    fi
    
    # Starte den Service neu
    log "Starte DeviceBox Service neu..."
    sudo systemctl daemon-reload
    sudo systemctl enable "$APP_NAME"
    sudo systemctl start "$APP_NAME"
    
    # Prüfe Service-Status
    sleep 3
    if sudo systemctl is-active --quiet "$APP_NAME"; then
        success "DeviceBox Service läuft erfolgreich"
    else
        error "DeviceBox Service konnte nicht gestartet werden"
        sudo systemctl status "$APP_NAME"
        return 1
    fi
    
    # Lösche Backup nach erfolgreichem Update
    sudo rm -rf "$BACKUP_DIR"
    
    success "Update abgeschlossen!"
    return 0
}

# Installiere Abhängigkeiten
install_dependencies() {
    log "Installiere System-Abhängigkeiten..."
    
    sudo apt update
    sudo apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        git \
        curl \
        unzip \
        systemd \
        nginx \
        ufw
    
    success "System-Abhängigkeiten installiert"
}

# Erstelle Installationsverzeichnis
create_directories() {
    log "Erstelle Installationsverzeichnisse..."
    
    sudo mkdir -p "$INSTALL_DIR"
    sudo mkdir -p "$INSTALL_DIR/data"
    sudo mkdir -p "$INSTALL_DIR/logs"
    sudo mkdir -p "$INSTALL_DIR/backup"
    
    # Debug: Prüfe ob SERVICE_USER korrekt gesetzt ist
    log "Setze Berechtigungen für Benutzer: $SERVICE_USER"
    
    # Prüfe ob der Benutzer existiert
    if ! id "$SERVICE_USER" &>/dev/null; then
        error "Benutzer '$SERVICE_USER' existiert nicht!"
        error "Verfügbare Benutzer:"
        cut -d: -f1 /etc/passwd | grep -v "^root$" | head -10
        exit 1
    fi
    
    # Setze Berechtigungen
    sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    sudo chmod 755 "$INSTALL_DIR"
    
    success "Verzeichnisse erstellt"
}

# Lade Anwendung herunter
download_app() {
    log "Lade DeviceBox herunter..."
    
    # Erstelle temporäres Verzeichnis
    temp_dir=$(mktemp -d)
    cd "$temp_dir"
    
    # Lade Repository herunter
    git clone "https://github.com/$GITHUB_REPO.git" "$APP_NAME"
    
    # Kopiere Dateien ins Installationsverzeichnis
    sudo cp -r "$APP_NAME"/* "$INSTALL_DIR/"
    
    # Setze Berechtigungen
    sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
sudo chmod +x "$INSTALL_DIR/app.py"
sudo chmod +x "$INSTALL_DIR/update.py"
sudo chmod +x "$INSTALL_DIR/update_simple.py"
sudo chmod +x "$INSTALL_DIR/update_curl.sh"
sudo chmod +x "$INSTALL_DIR/auto_update.py"
sudo chmod +x "$INSTALL_DIR/device_manager.py"
sudo chmod +x "$INSTALL_DIR/debug_update.py"
sudo chmod +x "$INSTALL_DIR/test_update.py"
    
    # Aufräumen
    cd /
    rm -rf "$temp_dir"
    
    success "Anwendung heruntergeladen"
}

# Installiere Python-Abhängigkeiten
install_python_deps() {
    log "Installiere Python-Abhängigkeiten..."
    
    cd "$INSTALL_DIR"
    
    # Erstelle virtuelle Umgebung
    python3 -m venv venv
    
    # Setze Berechtigungen für virtuelle Umgebung
    sudo chown -R "$SERVICE_USER:$SERVICE_USER" venv
    
    # Aktiviere virtuelle Umgebung
    source venv/bin/activate
    
    # Installiere Abhängigkeiten
    pip install --upgrade pip
    
    # Installiere Abhängigkeiten mit Fehlerbehandlung
    log "Installiere Python-Pakete..."
    if pip install -r requirements.txt; then
        success "Alle Python-Abhängigkeiten installiert"
    else
        warning "Einige Pakete konnten nicht installiert werden, versuche alternative Installation..."
        
        # Installiere Pakete einzeln mit flexibleren Versionen
        pip install Flask Werkzeug psutil requests python-dateutil python-dotenv colorlog
        
        # Versuche cryptography mit flexiblerer Version
        if ! pip install cryptography; then
            warning "cryptography konnte nicht installiert werden, überspringe..."
        fi
        
        success "Grundlegende Python-Abhängigkeiten installiert"
    fi
    
    success "Python-Abhängigkeiten installiert"
}

# Erstelle Systemd-Service
create_systemd_service() {
    log "Erstelle Systemd-Service..."
    
    cat << EOF | sudo tee /etc/systemd/system/devicebox.service > /dev/null
[Unit]
Description=DeviceBox - Raspberry Pi Device Management
After=network.target
Wants=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin
Environment=GITHUB_REPO=$GITHUB_REPO
Environment=APP_NAME=$APP_NAME
Environment=INSTALL_DIR=$INSTALL_DIR
Environment=DATA_DIR=$INSTALL_DIR/data
Environment=PORT=$PORT
Environment=HOST=$HOST
Environment=DEBUG=False
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=devicebox

[Install]
WantedBy=multi-user.target
EOF

    # Lade Systemd neu und aktiviere Service
    sudo systemctl daemon-reload
    sudo systemctl enable devicebox
    
    success "Systemd-Service erstellt und aktiviert"
}

# Konfiguriere Firewall
configure_firewall() {
    log "Konfiguriere Firewall..."
    
    # Aktiviere UFW falls nicht aktiv
    if ! sudo ufw status | grep -q "Status: active"; then
        sudo ufw --force enable
    fi
    
    # Erlaube SSH (falls aktiv)
    if sudo systemctl is-active --quiet ssh; then
        sudo ufw allow ssh
    fi
    
    # Erlaube DeviceBox Port
    sudo ufw allow "$PORT"
    
    success "Firewall konfiguriert"
}

# Konfiguriere Nginx (optional)
configure_nginx() {
    log "Konfiguriere Nginx Reverse Proxy..."
    
    cat << EOF | sudo tee /etc/nginx/sites-available/devicebox > /dev/null
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://$HOST:$PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

    # Aktiviere Site
    sudo ln -sf /etc/nginx/sites-available/devicebox /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    
    # Teste Konfiguration
    sudo nginx -t
    
    # Starte Nginx
    sudo systemctl enable nginx
    sudo systemctl restart nginx
    
    success "Nginx konfiguriert"
}

# Starte Service
start_service() {
    log "Starte DeviceBox Service..."
    
    sudo systemctl start devicebox
    
    # Warte kurz und prüfe Status
    sleep 3
    
    if sudo systemctl is-active --quiet devicebox; then
        success "DeviceBox Service läuft erfolgreich"
        
        # Zeige Status
        log "Service Status:"
        sudo systemctl status devicebox --no-pager -l
        
        # Zeige IP-Adresse
        ip_address=$(hostname -I | awk '{print $1}')
        log "DeviceBox ist verfügbar unter:"
        log "  http://$ip_address"
        log "  http://$ip_address:$PORT"
        
    else
        error "Service konnte nicht gestartet werden"
        sudo systemctl status devicebox --no-pager -l
        exit 1
    fi
}

# Hauptinstallation
main() {
    if [ "$EXISTING_INSTALLATION" = true ]; then
        log "=== DeviceBox Update ==="
        log "Bestehende Installation gefunden in: $INSTALL_DIR"
        log ""
        
        # Prüfe ob das Skript über curl ausgeführt wird
        CURL_EXECUTION=false
        INTERACTIVE_MODE=true
        
        # Prüfe verschiedene Ausführungskontexte
        if [ -t 0 ]; then
            # Terminal-Verbindung vorhanden
            CURL_EXECUTION=false
            INTERACTIVE_MODE=true
        else
            # Keine Terminal-Verbindung (wahrscheinlich curl)
            CURL_EXECUTION=true
            INTERACTIVE_MODE=false
        fi
        
        # Zusätzliche Prüfung: Ist stdin ein Pipe?
        if [ -p /dev/stdin ] || [ ! -t 0 ]; then
            CURL_EXECUTION=true
            INTERACTIVE_MODE=false
        fi
        
        # Prüfe ob das Skript über curl heruntergeladen wurde
        if [ -n "$SSH_CLIENT" ] || [ -n "$SSH_TTY" ]; then
            # SSH-Verbindung - wahrscheinlich interaktiv
            INTERACTIVE_MODE=true
            CURL_EXECUTION=false
        fi
        
        # Frage den Benutzer nach Bestätigung (außer bei --force-update oder curl)
        if [ "$FORCE_UPDATE" = false ] && [ "$INTERACTIVE_MODE" = true ]; then
            warning "DeviceBox ist bereits installiert!"
            warning "Dies wird ein Update der bestehenden Installation durchführen."
            echo ""
            echo "Möchten Sie fortfahren? (y/N)"
            read -r response
            
            if [[ ! "$response" =~ ^[Yy]$ ]]; then
                log "Update abgebrochen."
                exit 0
            fi
        else
            if [ "$FORCE_UPDATE" = true ]; then
                log "Force-Update aktiviert - Update ohne Bestätigung"
            else
                log "Automatisches Update über curl erkannt - Update ohne Bestätigung"
            fi
        fi
        
        # Debug-Informationen
        log "Ausführungskontext:"
        log "  Interactive Mode: $INTERACTIVE_MODE"
        log "  Curl Execution: $CURL_EXECUTION"
        log "  Force Update: $FORCE_UPDATE"
        
        # Führe Update durch
        check_system
        perform_update
        
        success "=== Update abgeschlossen! ==="
        log ""
        log "DeviceBox wurde erfolgreich aktualisiert"
        log "Die Anwendung läuft weiterhin automatisch nach jedem Neustart"
        log ""
        log "Nützliche Befehle:"
        log "  sudo systemctl status devicebox    # Service-Status"
        log "  sudo systemctl restart devicebox    # Service neu starten"
        log "  sudo journalctl -u devicebox -f     # Logs anzeigen"
        log ""
        log "Update-Befehle:"
        log "  python3 $INSTALL_DIR/auto_update.py # Auto-Update durchführen"
        log "  python3 $INSTALL_DIR/debug_update.py # Debug-Informationen"
        
    else
        log "=== DeviceBox Installation ==="
        
        check_system
        install_dependencies
        create_directories
        download_app
        install_python_deps
        create_systemd_service
        configure_firewall
        configure_nginx
        start_service
        
        success "=== Installation abgeschlossen! ==="
        log ""
        log "DeviceBox läuft jetzt auf diesem Raspberry Pi"
        log "Die Anwendung startet automatisch nach jedem Neustart"
        log ""
        log "Nützliche Befehle:"
        log "  sudo systemctl status devicebox    # Service-Status"
        log "  sudo systemctl restart devicebox    # Service neu starten"
        log "  sudo journalctl -u devicebox -f     # Logs anzeigen"
        log ""
        log "Update-Befehle:"
        log "  python3 $INSTALL_DIR/auto_update.py # Auto-Update durchführen"
        log "  python3 $INSTALL_DIR/debug_update.py # Debug-Informationen"
    fi
}

# Führe Installation aus
main "$@"
