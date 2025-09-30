# DeviceBox Debugging Guide

## Update-System Debugging

### Problem: Update-Funktion schlägt fehl

Wenn die Update-Funktion in der Web-Oberfläche fehlschlägt, können Sie folgende Debug-Schritte durchführen:

### 1. Debug-Skript ausführen

```bash
# Vollständiges Debug-System
sudo python3 /opt/devicebox/debug_update.py

# Nur Update-Check testen
sudo python3 /opt/devicebox/debug_update.py check

# Nur GitHub-Verbindung testen
sudo python3 /opt/devicebox/debug_update.py github
```

### 2. Einfacher Update-Test

```bash
# Einfacher Test des Update-Systems
sudo python3 /opt/devicebox/test_update.py
```

### 3. Manueller Update-Check

```bash
# Manueller Update-Check
sudo python3 /opt/devicebox/auto_update.py check
```

### 4. Service-Logs prüfen

```bash
# Aktuelle Logs anzeigen
sudo journalctl -u devicebox -f

# Letzte Logs anzeigen
sudo journalctl -u devicebox --since "1 hour ago"

# Service-Status prüfen
sudo systemctl status devicebox
```

### 5. Häufige Probleme und Lösungen

#### Problem: "Kein Update verfügbar" wird als Fehler angezeigt
**Lösung:** Das ist normal, wenn das System bereits aktuell ist. Die Web-Oberfläche zeigt jetzt eine entsprechende Nachricht.

#### Problem: GitHub-Verbindung fehlschlägt
**Lösung:** 
```bash
# Internet-Verbindung prüfen
ping github.com

# DNS-Auflösung prüfen
nslookup github.com
```

#### Problem: Berechtigungsfehler
**Lösung:**
```bash
# Berechtigungen korrigieren
sudo chown -R musikwieland:musikwieland /opt/devicebox
sudo chmod +x /opt/devicebox/*.py
```

#### Problem: Version-Datei fehlt oder ist korrupt
**Lösung:**
```bash
# Version-Datei neu erstellen
sudo python3 /opt/devicebox/auto_update.py check
```

### 6. Debug-Informationen sammeln

```bash
# System-Informationen
uname -a
python3 --version
lsb_release -a

# DeviceBox-Informationen
ls -la /opt/devicebox/
cat /opt/devicebox/version.json
```

### 7. Service neu starten

```bash
# Service neu starten
sudo systemctl restart devicebox

# Service-Status prüfen
sudo systemctl status devicebox
```

## USB-Geräte Debugging

### Problem: USB-Geräte werden nicht erkannt

```bash
# Verfügbare USB-Geräte anzeigen
lsusb

# Serielle Geräte anzeigen
ls /dev/tty*

# Geräte-Informationen
sudo dmesg | grep -i usb
```

### Problem: Geräte-Tests schlagen fehl

1. Prüfen Sie, ob das Gerät korrekt angeschlossen ist
2. Prüfen Sie die Geräte-Berechtigungen
3. Prüfen Sie die Geräte-Treiber

## Logs und Monitoring

### Service-Logs
```bash
# Live-Monitoring
sudo journalctl -u devicebox -f

# Logs der letzten Stunde
sudo journalctl -u devicebox --since "1 hour ago"

# Logs der letzten 24 Stunden
sudo journalctl -u devicebox --since "24 hours ago"
```

### Anwendungs-Logs
```bash
# DeviceBox-Logs
tail -f /opt/devicebox/logs/devicebox.log

# Update-Logs
tail -f /opt/devicebox/logs/update.log
```

## Support

Bei Problemen sammeln Sie bitte folgende Informationen:

1. Ausgabe von `sudo python3 /opt/devicebox/debug_update.py`
2. Service-Status: `sudo systemctl status devicebox`
3. Letzte Logs: `sudo journalctl -u devicebox --since "1 hour ago"`
4. System-Informationen: `uname -a` und `python3 --version`

Diese Informationen helfen bei der Fehlerdiagnose.
