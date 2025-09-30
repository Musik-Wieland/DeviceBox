# DeviceBox - Geräte-Setup Anleitung

Diese Anleitung beschreibt die Integration der spezifischen Geräte in das DeviceBox System.

## Unterstützte Geräte

| Gerätetyp | Modell | Features | Library |
|-----------|--------|----------|---------|
| Papierdrucker | Brother HL-L2340DW | Testdruck | CUPS |
| Label-Printer | Brother QL-700 | Testdruck, Labelgröße | brother_ql |
| Versandlabel-Printer | (noch nicht vorhanden) | Testdruck | brother_ql |
| Barcode-Scanner | Datalogic Touch 65 | Test-Scan | evdev |
| Bondrucker | Epson TM-T20II | Testdruck | python_escpos |
| EC-Kartengerät | Ingenico Move/3500 | Test-Transaktion | custom_sdk |

## Installation

### 1. System-Setup ausführen

```bash
# Führe das automatische Setup aus
sudo python3 device_setup.py
```

Das Setup-Skript installiert:
- System-Abhängigkeiten (CUPS, Treiber)
- Python-Bibliotheken
- USB-Berechtigungen
- Standard-Gerätekonfiguration

### 2. Manuelle Installation (falls automatisches Setup fehlschlägt)

#### System-Abhängigkeiten
```bash
# CUPS und Brother-Treiber
sudo apt-get update
sudo apt-get install -y cups cups-client printer-driver-brlaser

# Python-Entwicklungsumgebung
sudo apt-get install -y python3-pip python3-dev libusb-1.0-0-dev libudev-dev

# Python-Bibliotheken
pip3 install -r requirements.txt
```

#### USB-Berechtigungen konfigurieren
```bash
# Erstelle udev-Regeln
sudo tee /etc/udev/rules.d/99-devicebox.rules > /dev/null << 'EOF'
# Brother Drucker
SUBSYSTEM=="usb", ATTRS{idVendor}=="04f9", MODE="0666", GROUP="plugdev"

# Epson Bondrucker
SUBSYSTEM=="usb", ATTRS{idVendor}=="04b8", MODE="0666", GROUP="plugdev"

# Datalogic Scanner
SUBSYSTEM=="usb", ATTRS{idVendor}=="05f9", MODE="0666", GROUP="plugdev"

# Ingenico Payment Terminal
SUBSYSTEM=="usb", ATTRS{idVendor}=="0bda", MODE="0666", GROUP="plugdev"
EOF

# Lade udev-Regeln neu
sudo udevadm control --reload-rules
sudo udevadm trigger

# Füge Benutzer zur plugdev-Gruppe hinzu
sudo usermod -a -G plugdev $USER
```

## Geräte-spezifische Konfiguration

### Brother HL-L2340DW (Papierdrucker)

1. **CUPS konfigurieren:**
   ```bash
   # CUPS-Service starten
   sudo systemctl start cups
   sudo systemctl enable cups
   
   # Web-Interface öffnen
   # http://localhost:631
   ```

2. **Drucker hinzufügen:**
   - Öffne CUPS Web-Interface
   - "Add Printer" klicken
   - Brother HL-L2340DW auswählen
   - Treiber: "Brother HL-L2340DW for CUPS"

3. **Test:**
   - Über DeviceBox Web-Interface: Gerät hinzufügen → Testdruck

### Brother QL-700 (Label-Printer)

1. **Gerät anschließen:**
   ```bash
   # Prüfe USB-Verbindung
   lsusb | grep Brother
   # Sollte zeigen: Bus 001 Device 003: ID 04f9:2042 Brother Industries, Ltd
   ```

2. **Test-Label erstellen:**
   ```python
   from brother_ql.conversion import convert
   from brother_ql.backends.helpers import send
   from brother_ql.raster import BrotherQLRaster
   
   qlr = BrotherQLRaster('QL-700')
   instructions = convert(
       qlr=qlr,
       images=['test_label.png'],
       label='62',  # 62x100mm
       rotate='auto'
   )
   send(instructions=instructions, printer_identifier='usb://0x04f9:0x2042')
   ```

3. **Über DeviceBox:**
   - Gerät hinzufügen → Brother QL-700 auswählen
   - Testdruck durchführen

### Epson TM-T20II (Bondrucker)

1. **Gerät anschließen:**
   ```bash
   # Prüfe USB-Verbindung
   lsusb | grep Epson
   # Sollte zeigen: Bus 001 Device 004: ID 04b8:0e15 Seiko Epson Corp.
   ```

2. **Test-Beleg drucken:**
   ```python
   from escpos.printer import Usb
   
   p = Usb(0x04b8, 0x0e15)
   p.text("DeviceBox Test\n")
   p.text("Epson TM-T20II\n")
   p.cut()
   ```

3. **Über DeviceBox:**
   - Gerät hinzufügen → Epson TM-T20II auswählen
   - Testdruck durchführen

### Datalogic Touch 65 (Barcode-Scanner)

1. **Gerät anschließen:**
   ```bash
   # Prüfe USB-Verbindung
   lsusb | grep Datalogic
   # Sollte zeigen: Bus 001 Device 005: ID 05f9:2214 PSC Scanning, Inc.
   ```

2. **Scanner-Test:**
   ```python
   import evdev
   
   # Suche nach Datalogic-Geräten
   devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
   for device in devices:
       if 'Datalogic' in device.name:
           print(f"Scanner gefunden: {device.name}")
   ```

3. **Über DeviceBox:**
   - Gerät hinzufügen → Datalogic Touch 65 auswählen
   - Test-Scan durchführen

### Ingenico Move/3500 (EC-Kartengerät)

1. **Gerät anschließen:**
   ```bash
   # Prüfe USB-Verbindung
   lsusb | grep Ingenico
   # Sollte zeigen: Bus 001 Device 006: ID 0bda:0161 Realtek Semiconductor Corp.
   ```

2. **SDK-Integration:**
   - Kontaktiere Ingenico für SDK-Zugang
   - Befolge die Ingenico-Dokumentation
   - Integriere SDK in DeviceBox

3. **Über DeviceBox:**
   - Gerät hinzufügen → Ingenico Move/3500 auswählen
   - Test-Transaktion durchführen

## Troubleshooting

### Häufige Probleme

#### 1. USB-Gerät wird nicht erkannt
```bash
# Prüfe USB-Verbindung
lsusb

# Prüfe udev-Regeln
sudo udevadm info --query=all --name=/dev/bus/usb/001/003

# Prüfe Berechtigungen
groups $USER
```

#### 2. Brother QL-700 funktioniert nicht
```bash
# Prüfe brother_ql Installation
python3 -c "import brother_ql; print('OK')"

# Prüfe USB-Zugriff
sudo python3 -c "import usb.core; print(usb.core.find(idVendor=0x04f9))"
```

#### 3. Epson TM-T20II druckt nicht
```bash
# Prüfe python-escpos Installation
python3 -c "from escpos.printer import Usb; print('OK')"

# Prüfe USB-Zugriff
sudo python3 -c "import usb.core; print(usb.core.find(idVendor=0x04b8))"
```

#### 4. Datalogic Scanner wird nicht erkannt
```bash
# Prüfe evdev Installation
python3 -c "import evdev; print('OK')"

# Prüfe Input-Geräte
ls /dev/input/
cat /proc/bus/input/devices | grep -A5 Datalogic
```

### Logs prüfen

```bash
# DeviceBox Logs
sudo journalctl -u devicebox -f

# CUPS Logs
sudo tail -f /var/log/cups/error_log

# System Logs
sudo dmesg | grep -i usb
```

### Berechtigungen prüfen

```bash
# Prüfe Gruppenmitgliedschaft
groups $USER

# Füge zu Gruppen hinzu (falls nötig)
sudo usermod -a -G lp,plugdev $USER

# Logout und Login erforderlich
```

## Erweiterte Konfiguration

### CUPS-Drucker konfigurieren

```bash
# Drucker-Liste anzeigen
lpstat -p

# Drucker-Test
echo "Test" | lp -d Brother_HL_L2340DW

# Drucker-Einstellungen
lpoptions -p Brother_HL_L2340DW -l
```

### Brother QL-700 Label-Größen

| Label-Typ | Größe | Code |
|-----------|-------|------|
| 62x100mm | Standard | 62 |
| 62x50mm | Klein | 50 |
| 29x90mm | Schmales Label | 29 |

### Epson TM-T20II ESC/POS-Befehle

```python
# Spezielle Befehle
p.set(align='center')  # Zentrieren
p.set(font='b')        # Fett
p.text("Test\n")
p.cut()                # Schneiden
```

## Support

Bei Problemen:

1. **Logs prüfen:** `sudo journalctl -u devicebox -f`
2. **USB-Verbindung testen:** `lsusb`
3. **Bibliotheken testen:** `python3 -c "import [library_name]"`
4. **GitHub Issue erstellen:** Mit Logs und Geräteinformationen

## Nächste Schritte

Nach erfolgreicher Installation:

1. Geräte anschließen
2. DeviceBox neu starten: `sudo systemctl restart devicebox`
3. Weboberfläche öffnen: `http://[IP-Adresse]`
4. Geräte hinzufügen und testen
5. Automatische Erkennung aktivieren
