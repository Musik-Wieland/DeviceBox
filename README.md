# DeviceBox - Raspberry Pi Web Interface

Ein modernes, Apple-inspiriertes Web-Interface für Raspberry Pi mit automatischen Updates und Systemüberwachung.

## 🚀 Features

- **Moderne Web-Oberfläche** mit Apple-Design und flüssigen Animationen
- **Automatische Updates** über GitHub mit Datenverlust-Schutz
- **Systemüberwachung** in Echtzeit (CPU, RAM, Festplatte, Temperatur)
- **Einzeiler Installation** über GitHub
- **Automatischer Start** nach jedem Neustart
- **Responsive Design** für alle Geräte

## 📋 Systemanforderungen

- Raspberry Pi (alle Modelle)
- Raspberry Pi OS (Debian-basiert)
- Python 3.7+
- Internetverbindung für Updates

## ⚡ Schnellstart

### Einzeiler Installation

```bash
curl -sSL https://raw.githubusercontent.com/yourusername/devicebox/main/install.sh | bash
```

### Manuelle Installation

1. **Repository klonen:**
   ```bash
   git clone https://github.com/yourusername/devicebox.git
   cd devicebox
   ```

2. **Installation ausführen:**
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

3. **Web-Interface öffnen:**
   ```
   http://[IP-ADRESSE]:5000
   ```

## 🎨 Web-Interface

Das Web-Interface bietet folgende Funktionen:

### Dashboard
- **Version anzeigen** - Aktuelle Software-Version
- **Update-Check** - Automatische Prüfung auf neue Versionen
- **Update-Installation** - Ein-Klick Updates ohne Datenverlust
- **Gerätestatus** - Echtzeit-Monitoring aller Systemressourcen

### Systemüberwachung
- **CPU-Auslastung** und Temperatur
- **Arbeitsspeicher** Verwendung und Verfügbarkeit
- **Festplatten-Speicher** und I/O-Statistiken
- **Netzwerk-Verbindungen** und Uptime
- **Service-Status** wichtiger Systemdienste

### System-Aktionen
- **System-Neustart** mit Bestätigung
- **Status-Aktualisierung** manuell
- **Update-Logs** für Transparenz

## 🔧 Konfiguration

### Service-Verwaltung

```bash
# Status anzeigen
sudo systemctl status devicebox

# Service neustarten
sudo systemctl restart devicebox

# Service stoppen
sudo systemctl stop devicebox

# Logs anzeigen
sudo journalctl -u devicebox -f
```

### Update-Konfiguration

Das Update-System kann in `update_manager.py` konfiguriert werden:

```python
# GitHub Repository URL
self.repo_url = "https://github.com/yourusername/devicebox.git"

# Backup-Verzeichnis
self.backup_dir = os.path.join(self.current_dir, 'backup')
```

## 📁 Projektstruktur

```
devicebox/
├── app.py                 # Hauptanwendung (Flask)
├── update_manager.py      # Update-System
├── device_monitor.py      # Systemüberwachung
├── requirements.txt       # Python-Abhängigkeiten
├── devicebox.service      # Systemd Service
├── install.sh            # Installationsskript
├── version.json          # Versionsinformationen
├── templates/
│   └── index.html        # Web-Interface Template
└── static/
    ├── css/
    │   └── style.css     # Apple-inspiriertes Design
    └── js/
        └── app.js        # Frontend JavaScript
```

## 🔄 Update-System

### Automatische Updates

Das System unterstützt automatische Updates über GitHub:

1. **Version prüfen** - GitHub API für neueste Releases
2. **Backup erstellen** - Vollständiges Backup vor Update
3. **Update durchführen** - Repository klonen und Dateien kopieren
4. **Backup wiederherstellen** - Bei Fehlern automatische Wiederherstellung

### Update-Prozess

```python
# Update-Check
update_info = update_manager.check_for_updates()

# Update durchführen
result = update_manager.perform_update()
```

## 🛡️ Sicherheit

### Service-Sicherheit
- **Eingeschränkte Berechtigungen** - Läuft als Benutzer 'pi'
- **Systemd-Sicherheit** - NoNewPrivileges, PrivateTmp
- **Firewall-Konfiguration** - Nur notwendige Ports geöffnet

### Update-Sicherheit
- **Backup-System** - Automatische Sicherung vor Updates
- **Rollback-Funktion** - Wiederherstellung bei Fehlern
- **Validierung** - Überprüfung der Update-Integrität

## 🔍 Troubleshooting

### Häufige Probleme

**Service startet nicht:**
```bash
sudo journalctl -u devicebox -f
```

**Web-Interface nicht erreichbar:**
```bash
# Firewall prüfen
sudo ufw status

# Port prüfen
sudo netstat -tlnp | grep 5000
```

**Update-Fehler:**
```bash
# Logs prüfen
sudo journalctl -u devicebox -f

# Manueller Update-Check
python3 -c "from update_manager import UpdateManager; print(UpdateManager().check_for_updates())"
```

### Debug-Modus

Für Entwicklung kann der Debug-Modus aktiviert werden:

```python
# In app.py
app.run(host='0.0.0.0', port=5000, debug=True)
```

## 📝 API-Endpunkte

### Status-Endpunkte
- `GET /api/status` - Gerätestatus abrufen
- `GET /api/version` - Aktuelle Version
- `GET /api/check-updates` - Update-Check
- `POST /api/update` - Update durchführen
- `POST /api/reboot` - System neustarten

### Beispiel-Response

```json
{
  "timestamp": "2024-01-01T12:00:00",
  "system": {
    "hostname": "raspberrypi",
    "platform": "Linux",
    "release": "5.15.0"
  },
  "cpu": {
    "usage_percent": 15.2,
    "count": 4,
    "frequency": {"current": 1500.0}
  },
  "memory": {
    "total": 4294967296,
    "available": 2147483648,
    "usage_percent": 50.0
  }
}
```

## 🤝 Beitragen

1. Fork das Repository
2. Erstelle einen Feature-Branch
3. Committe deine Änderungen
4. Push zum Branch
5. Erstelle einen Pull Request

## 📄 Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Siehe `LICENSE` für Details.

## 🙏 Danksagungen

- **Apple** für das Design-Inspiration
- **Flask** für das Web-Framework
- **Font Awesome** für die Icons
- **Raspberry Pi Foundation** für die Hardware

## 📞 Support

Bei Problemen oder Fragen:

1. **Issues** auf GitHub erstellen
2. **Logs** bereitstellen: `sudo journalctl -u devicebox -f`
3. **System-Info** angeben: `uname -a && python3 --version`

---

**DeviceBox** - Moderne Raspberry Pi Verwaltung mit Style! 🍎✨
