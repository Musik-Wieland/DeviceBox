#!/bin/bash
"""
DeviceBox Installation Fix
Behebt die Probleme bei der Installation
"""

set -e

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log "=== DeviceBox Installation Fix ==="

# 1. Installiere fehlende System-Abhängigkeiten
log "Installiere fehlende System-Abhängigkeiten..."
sudo apt-get update
sudo apt-get install -y \
    libcups2-dev \
    libcupsimage2-dev \
    build-essential \
    pkg-config \
    python3-dev \
    libusb-1.0-0-dev \
    libudev-dev

success "System-Abhängigkeiten installiert"

# 2. Installiere Python-Bibliotheken einzeln
log "Installiere Python-Bibliotheken..."

cd /opt/devicebox

# Installiere pycups separat
log "Installiere pycups..."
if pip install pycups; then
    success "pycups installiert"
else
    warning "pycups konnte nicht installiert werden - CUPS-Funktionen eingeschränkt"
fi

# Installiere evdev
log "Installiere evdev..."
if pip install evdev; then
    success "evdev installiert"
else
    warning "evdev konnte nicht installiert werden - Scanner-Funktionen eingeschränkt"
fi

# Installiere brother_ql
log "Installiere brother_ql..."
if pip install brother-ql; then
    success "brother_ql installiert"
else
    warning "brother_ql konnte nicht installiert werden - Label-Drucker eingeschränkt"
fi

# Installiere python-escpos
log "Installiere python-escpos..."
if pip install python-escpos; then
    success "python-escpos installiert"
else
    warning "python-escpos konnte nicht installiert werden - Bondrucker eingeschränkt"
fi

# Installiere Pillow
log "Installiere Pillow..."
if pip install Pillow; then
    success "Pillow installiert"
else
    warning "Pillow konnte nicht installiert werden - Bildverarbeitung eingeschränkt"
fi

# Installiere keyboard
log "Installiere keyboard..."
if pip install keyboard; then
    success "keyboard installiert"
else
    warning "keyboard konnte nicht installiert werden - Scanner-Input eingeschränkt"
fi

# Installiere hidapi
log "Installiere hidapi..."
if pip install hidapi; then
    success "hidapi installiert"
else
    warning "hidapi konnte nicht installiert werden - USB HID eingeschränkt"
fi

# 3. Konfiguriere USB-Berechtigungen
log "Konfiguriere USB-Berechtigungen..."

# Erstelle udev-Regeln
sudo tee /etc/udev/rules.d/99-devicebox.rules > /dev/null << 'EOF'
# DeviceBox USB-Berechtigungen
# Brother Drucker
SUBSYSTEM=="usb", ATTRS{idVendor}=="04f9", MODE="0666", GROUP="plugdev"

# Epson Bondrucker
SUBSYSTEM=="usb", ATTRS{idVendor}=="04b8", MODE="0666", GROUP="plugdev"

# Datalogic Scanner
SUBSYSTEM=="usb", ATTRS{idVendor}=="05f9", MODE="0666", GROUP="plugdev"

# Ingenico Payment Terminal
SUBSYSTEM=="usb", ATTRS{idVendor}=="0bda", MODE="0666", GROUP="plugdev"
EOF

# Setze korrekte Berechtigungen
sudo chmod 644 /etc/udev/rules.d/99-devicebox.rules

# Lade udev-Regeln neu
sudo udevadm control --reload-rules
sudo udevadm trigger

# Füge pi-Benutzer zur plugdev-Gruppe hinzu
sudo usermod -a -G plugdev pi

success "USB-Berechtigungen konfiguriert"

# 4. Konfiguriere sudo-Berechtigungen für Updates
log "Konfiguriere Update-Berechtigungen..."

# Erstelle sudoers-Eintrag
sudo tee /etc/sudoers.d/devicebox_pi > /dev/null << 'EOF'
# DeviceBox Update-Berechtigungen für pi
pi ALL=(ALL) NOPASSWD: /usr/bin/python3 /opt/devicebox/update_system.py update
pi ALL=(ALL) NOPASSWD: /usr/bin/python3 /opt/devicebox/update_system.py check
pi ALL=(ALL) NOPASSWD: /opt/devicebox/venv/bin/python /opt/devicebox/update_system.py update
pi ALL=(ALL) NOPASSWD: /opt/devicebox/venv/bin/python /opt/devicebox/update_system.py check
EOF

# Setze korrekte Berechtigungen
sudo chmod 440 /etc/sudoers.d/devicebox_pi

# Validiere sudoers-Syntax
if sudo visudo -c; then
    success "Update-Berechtigungen konfiguriert"
else
    error "Sudoers-Syntax-Fehler - manuelle Korrektur erforderlich"
fi

# 5. Teste Installation
log "Teste Installation..."

# Teste Python-Bibliotheken
python3 -c "
try:
    import flask
    print('✓ Flask verfügbar')
except ImportError:
    print('✗ Flask nicht verfügbar')

try:
    import psutil
    print('✓ psutil verfügbar')
except ImportError:
    print('✗ psutil nicht verfügbar')

try:
    import evdev
    print('✓ evdev verfügbar')
except ImportError:
    print('✗ evdev nicht verfügbar')

try:
    import brother_ql
    print('✓ brother_ql verfügbar')
except ImportError:
    print('✗ brother_ql nicht verfügbar')

try:
    import escpos
    print('✓ python-escpos verfügbar')
except ImportError:
    print('✗ python-escpos nicht verfügbar')

try:
    import PIL
    print('✓ Pillow verfügbar')
except ImportError:
    print('✗ Pillow nicht verfügbar')
"

# 6. Starte Service neu
log "Starte DeviceBox Service neu..."
sudo systemctl daemon-reload
sudo systemctl restart devicebox

# Warte kurz und prüfe Status
sleep 3
if sudo systemctl is-active --quiet devicebox; then
    success "DeviceBox Service läuft"
else
    error "DeviceBox Service startet nicht"
    log "Service-Logs:"
    sudo journalctl -u devicebox --no-pager -n 20
fi

# 7. Zeige Status
log "=== Installation Fix abgeschlossen ==="
log ""
log "Nächste Schritte:"
log "1. Öffne DeviceBox Web-Interface: http://$(hostname -I | awk '{print $1}')"
log "2. Prüfe Geräteerkennung"
log "3. Teste Scanner-Funktionen"
log ""
log "CUPS Web-Interface: http://localhost:631"
log "DeviceBox Logs: sudo journalctl -u devicebox -f"
log ""
log "Bei Problemen:"
log "- Prüfe Logs: sudo journalctl -u devicebox -f"
log "- Teste Scanner: sudo python3 /opt/devicebox/device_manager.py"
log "- Prüfe USB-Geräte: lsusb"
