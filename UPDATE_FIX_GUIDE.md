# DeviceBox Update-Fix Anleitung

## Problem
Das Update über die GUI schlägt fehl mit dem Fehler:
```
Update fehlgeschlagen: Unerwarteter Fehler: [Errno 2] No such file or directory: 'sudo'
```

## Ursache
Der DeviceBox-Service läuft als normaler Benutzer (`pi`), aber das Update-System benötigt Root-Rechte für:
- Backup-Erstellung in `/opt/devicebox_backup_*`
- Installation neuer Dateien in `/opt/devicebox`
- Service-Neustart

## Lösung

### Automatische Lösung (Empfohlen)

```bash
# Führe das sudoers-Setup aus
sudo python3 /opt/devicebox/setup_sudoers.py
```

### Manuelle Lösung

1. **Erstelle sudoers-Eintrag:**
   ```bash
   sudo nano /etc/sudoers.d/devicebox_pi
   ```

2. **Füge folgenden Inhalt hinzu:**
   ```
   # DeviceBox Update-Berechtigungen für pi
   pi ALL=(ALL) NOPASSWD: /usr/bin/python3 /opt/devicebox/update_system.py update
   pi ALL=(ALL) NOPASSWD: /usr/bin/python3 /opt/devicebox/update_system.py check
   pi ALL=(ALL) NOPASSWD: /opt/devicebox/venv/bin/python /opt/devicebox/update_system.py update
   pi ALL=(ALL) NOPASSWD: /opt/devicebox/venv/bin/python /opt/devicebox/update_system.py check
   ```

3. **Setze korrekte Berechtigungen:**
   ```bash
   sudo chmod 440 /etc/sudoers.d/devicebox_pi
   ```

4. **Validiere sudoers-Syntax:**
   ```bash
   sudo visudo -c
   ```

### Test der Konfiguration

```bash
# Teste sudo-Zugriff
sudo -u pi sudo -n /usr/bin/python3 /opt/devicebox/update_system.py check
```

### Service neu starten

```bash
# Starte DeviceBox-Service neu
sudo systemctl restart devicebox

# Prüfe Service-Status
sudo systemctl status devicebox
```

## Alternative Lösungen

### 1. Service als Root laufen lassen (Weniger sicher)

**devicebox.service bearbeiten:**
```bash
sudo nano /etc/systemd/system/devicebox.service
```

**Ändere:**
```ini
[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/devicebox
# ... rest bleibt gleich
```

**Service neu laden:**
```bash
sudo systemctl daemon-reload
sudo systemctl restart devicebox
```

### 2. Manuelle Updates

Falls die GUI-Updates weiterhin nicht funktionieren:

```bash
# Manuelles Update
sudo python3 /opt/devicebox/update_system.py update

# Service neu starten
sudo systemctl restart devicebox
```

## Troubleshooting

### Sudoers-Syntax-Fehler
```bash
# Validiere sudoers-Datei
sudo visudo -c -f /etc/sudoers.d/devicebox_pi

# Falls Fehler: Datei bearbeiten
sudo visudo /etc/sudoers.d/devicebox_pi
```

### Service startet nicht
```bash
# Prüfe Service-Status
sudo systemctl status devicebox

# Prüfe Logs
sudo journalctl -u devicebox -f

# Prüfe Berechtigungen
ls -la /opt/devicebox/
```

### Update funktioniert immer noch nicht
```bash
# Teste Update-Skript direkt
sudo python3 /opt/devicebox/update_system.py check

# Prüfe Python-Pfad
which python3
/opt/devicebox/venv/bin/python --version
```

## Sicherheitshinweise

- Der sudoers-Eintrag erlaubt nur die Ausführung des Update-Skripts
- Keine allgemeinen Root-Rechte für den Service-Benutzer
- Regelmäßige Überprüfung der sudoers-Datei empfohlen

## Verifikation

Nach der Konfiguration sollte das Update über die GUI funktionieren:

1. Öffne DeviceBox Web-Interface
2. Klicke "Auf Updates prüfen"
3. Bei verfügbarem Update: "Update installieren" klicken
4. Update sollte ohne Fehler durchgeführt werden

## Support

Bei weiteren Problemen:
- Prüfe Logs: `sudo journalctl -u devicebox -f`
- Teste manuell: `sudo python3 /opt/devicebox/update_system.py update`
- Erstelle GitHub Issue mit Logs
