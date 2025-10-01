# DeviceBox Installation Fix

## Problem
Die Installation schlägt fehl wegen:
- `pycups` kann nicht kompiliert werden (CUPS-Header fehlen)
- USB-Berechtigungen können nicht gesetzt werden
- Einige Python-Bibliotheken fehlen
- Service startet nicht

## Lösung

### Automatische Reparatur (Empfohlen)

```bash
# Lade das Fix-Skript herunter und führe es aus
curl -fsSL https://raw.githubusercontent.com/Musik-Wieland/DeviceBox/main/fix_installation.sh | bash
```

### Manuelle Reparatur

#### 1. System-Abhängigkeiten installieren

```bash
sudo apt-get update
sudo apt-get install -y \
    libcups2-dev \
    libcupsimage2-dev \
    build-essential \
    pkg-config \
    python3-dev \
    libusb-1.0-0-dev \
    libudev-dev
```

#### 2. Python-Bibliotheken einzeln installieren

```bash
cd /opt/devicebox

# Installiere pycups
pip install pycups

# Installiere evdev (für Scanner)
pip install evdev

# Installiere brother_ql (für Label-Drucker)
pip install brother-ql

# Installiere python-escpos (für Bondrucker)
pip install python-escpos

# Installiere Pillow (für Bildverarbeitung)
pip install Pillow

# Installiere keyboard (für Scanner-Input)
pip install keyboard

# Installiere hidapi (für USB HID)
pip install hidapi
```

#### 3. USB-Berechtigungen konfigurieren

```bash
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

# Setze Berechtigungen
sudo chmod 644 /etc/udev/rules.d/99-devicebox.rules

# Lade udev-Regeln neu
sudo udevadm control --reload-rules
sudo udevadm trigger

# Füge pi-Benutzer zur plugdev-Gruppe hinzu
sudo usermod -a -G plugdev pi
```

#### 4. Update-Berechtigungen konfigurieren

```bash
# Erstelle sudoers-Eintrag für Updates
sudo tee /etc/sudoers.d/devicebox_pi > /dev/null << 'EOF'
# DeviceBox Update-Berechtigungen für pi
pi ALL=(ALL) NOPASSWD: /usr/bin/python3 /opt/devicebox/update_system.py update
pi ALL=(ALL) NOPASSWD: /usr/bin/python3 /opt/devicebox/update_system.py check
pi ALL=(ALL) NOPASSWD: /opt/devicebox/venv/bin/python /opt/devicebox/update_system.py update
pi ALL=(ALL) NOPASSWD: /opt/devicebox/venv/bin/python /opt/devicebox/update_system.py check
EOF

# Setze Berechtigungen
sudo chmod 440 /etc/sudoers.d/devicebox_pi

# Validiere Syntax
sudo visudo -c
```

#### 5. Service neu starten

```bash
# Service neu laden und starten
sudo systemctl daemon-reload
sudo systemctl restart devicebox

# Status prüfen
sudo systemctl status devicebox
```

### Test der Installation

```bash
# Teste Python-Bibliotheken
python3 -c "
import flask
import psutil
import evdev
import brother_ql
import escpos
import PIL
print('Alle Bibliotheken verfügbar!')
"

# Teste USB-Geräte
lsusb | grep -E "(Brother|Epson|Datalogic|Ingenico)"

# Teste Scanner-Erkennung
python3 -c "
from device_manager import USBDeviceManager
dm = USBDeviceManager()
devices = dm.get_available_usb_devices()
print('Verfügbare Geräte:', len(devices))
"
```

### Troubleshooting

#### Service startet nicht

```bash
# Prüfe Logs
sudo journalctl -u devicebox -f

# Prüfe Python-Pfad
ls -la /opt/devicebox/venv/bin/python

# Teste manuell
cd /opt/devicebox
python3 app.py
```

#### Bibliotheken fehlen

```bash
# Prüfe Installation
pip list | grep -E "(flask|psutil|evdev|brother|escpos|pillow)"

# Installiere fehlende Pakete
pip install [paket-name]
```

#### USB-Geräte werden nicht erkannt

```bash
# Prüfe udev-Regeln
cat /etc/udev/rules.d/99-devicebox.rules

# Prüfe Gruppenmitgliedschaft
groups pi

# Teste USB-Zugriff
sudo python3 -c "
import usb.core
print('USB-Geräte:', len(list(usb.core.find(find_all=True))))
"
```

#### Scanner funktioniert nicht

```bash
# Prüfe evdev-Installation
python3 -c "import evdev; print('evdev OK')"

# Prüfe Input-Geräte
ls /dev/input/

# Teste Scanner-Erkennung
python3 -c "
import evdev
devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
for device in devices:
    if 'datalogic' in device.name.lower() or 'psc' in device.name.lower():
        print(f'Scanner gefunden: {device.name} ({device.path})')
"
```

### Nach der Reparatur

1. **Web-Interface öffnen:** `http://[IP-Adresse]`
2. **Scanner-Sektion prüfen:** Sollte Datalogic Touch 65 anzeigen
3. **Scanner verbinden:** "Verbinden"-Button klicken
4. **Test-Scan:** Barcode scannen und Ergebnis prüfen

### Support

Bei weiteren Problemen:
- Prüfe Logs: `sudo journalctl -u devicebox -f`
- Teste manuell: `cd /opt/devicebox && python3 app.py`
- Erstelle GitHub Issue mit Logs
