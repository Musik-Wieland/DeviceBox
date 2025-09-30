# DeviceBox - Raspberry Pi Management System

Ein modernes, Apple-inspiriertes Management-System für Raspberry Pi mit automatischen Updates und einer eleganten Weboberfläche.

## Features

- 🌐 **Lokale Weboberfläche** - Zugriff über IP-Adresse
- 🔄 **Automatische Updates** - GitHub-Integration ohne Datenverlust
- 🚀 **Einzeiler Installation** - Universelles Installationsskript
- 🔧 **Autostart** - Startet automatisch nach jedem Neustart
- 📊 **Gerätestatus** - Echtzeit-Monitoring von CPU, RAM, Speicher
- 🎨 **Apple Design** - Liquid Glass Design wie bei Apple-Produkten
- 📱 **Responsive** - Funktioniert auf Desktop und Mobile

## Installation

### Schnellinstallation

```bash
curl -fsSL https://raw.githubusercontent.com/Musik-Wieland/DeviceBox/main/install.sh | bash
```

### Manuelle Installation

1. Repository klonen:
```bash
git clone https://github.com/Musik-Wieland/DeviceBox.git
cd devicebox
```

2. Installationsskript ausführen:
```bash
chmod +x install.sh
./install.sh
```

## Deinstallation

### Vollständige Deinstallation

**Interaktive Deinstallation:**
```bash
curl -fsSL https://raw.githubusercontent.com/Musik-Wieland/DeviceBox/main/uninstall.sh | bash
```

**Automatische Deinstallation (ohne Nachfrage):**
```bash
curl -fsSL https://raw.githubusercontent.com/Musik-Wieland/DeviceBox/main/uninstall.sh | bash -s -- --force
```

### Manuelle Deinstallation

```bash
chmod +x uninstall.sh
./uninstall.sh          # Interaktive Deinstallation
./uninstall.sh --force   # Automatische Deinstallation
```

Das Deinstallationsskript entfernt:
- ✅ DeviceBox Service (systemd)
- ✅ Installationsverzeichnis (`/opt/devicebox`)
- ✅ Nginx-Konfiguration
- ✅ Firewall-Regeln
- ✅ Python-Abhängigkeiten (optional)
- ✅ System-Abhängigkeiten (optional)
- ✅ Temporäre Dateien und Logs

### Schnell-Deinstallation (für erfahrene Benutzer)

```bash
# Service stoppen und entfernen
sudo systemctl stop devicebox
sudo systemctl disable devicebox
sudo rm -f /etc/systemd/system/devicebox.service
sudo systemctl daemon-reload

# Installationsverzeichnis entfernen
sudo rm -rf /opt/devicebox

# Nginx-Konfiguration entfernen
sudo rm -f /etc/nginx/sites-available/devicebox
sudo rm -f /etc/nginx/sites-enabled/devicebox
sudo systemctl reload nginx

# Firewall-Regel entfernen
sudo ufw delete allow 8080
```

### Konfiguration

Vor der Installation können Umgebungsvariablen gesetzt werden:

```bash
export GITHUB_REPO="Musik-Wieland/DeviceBox"
export APP_NAME="devicebox"
export INSTALL_DIR="/opt/devicebox"
export SERVICE_USER="musikwieland"
export PORT="8080"
export HOST="0.0.0.0"
```

## Verwendung

### Weboberfläche

Nach der Installation ist DeviceBox verfügbar unter:
- `http://[IP-Adresse]` (über Nginx)
- `http://[IP-Adresse]:8080` (direkt)

### Service-Management

```bash
# Service-Status prüfen
sudo systemctl status devicebox

# Service neu starten
sudo systemctl restart devicebox

# Service stoppen
sudo systemctl stop devicebox

# Service starten
sudo systemctl start devicebox

# Logs anzeigen
sudo journalctl -u devicebox -f
```

### Updates

#### Automatisches Update über Weboberfläche
1. Öffne die Weboberfläche
2. Klicke auf "Auf Updates prüfen"
3. Bei verfügbarem Update: "Update installieren" klicken

#### Manuelles Update
```bash
# Service stoppen
sudo systemctl stop devicebox

# Update durchführen
python3 /opt/devicebox/update.py

# Service starten
sudo systemctl start devicebox
```

## Projektstruktur

```
devicebox/
├── app.py                 # Hauptanwendung (Flask)
├── update.py              # Update-System
├── install.sh             # Installationsskript
├── devicebox.service      # Systemd-Service
├── requirements.txt       # Python-Abhängigkeiten
├── config.env.example     # Konfigurationsvorlage
├── templates/
│   └── index.html         # Weboberfläche
├── static/
│   ├── css/
│   │   └── style.css      # Apple-inspiriertes Design
│   └── js/
│       └── app.js         # Frontend-Logik
└── README.md              # Diese Datei
```

## API-Endpunkte

- `GET /` - Hauptseite
- `GET /api/status` - Gerätestatus
- `GET /api/version` - Aktuelle Version
- `GET /api/check-updates` - Update-Check
- `POST /api/update` - Update durchführen

## Konfiguration

### Umgebungsvariablen

| Variable | Standard | Beschreibung |
|----------|----------|--------------|
| `GITHUB_REPO` | `Musik-Wieland/DeviceBox` | GitHub Repository |
| `APP_NAME` | `devicebox` | Anwendungsname |
| `INSTALL_DIR` | `/opt/devicebox` | Installationsverzeichnis |
| `DATA_DIR` | `/opt/devicebox/data` | Datenverzeichnis |
| `SERVICE_USER` | `musikwieland` | Service-Benutzer |
| `HOST` | `0.0.0.0` | Web-Server Host |
| `PORT` | `8080` | Web-Server Port |
| `DEBUG` | `False` | Debug-Modus |

### Konfigurationsdatei

Erstelle eine `config.env` Datei basierend auf `config.env.example`:

```bash
cp config.env.example config.env
# Bearbeite config.env nach Bedarf
```

## Entwicklung

### Lokale Entwicklung

1. Repository klonen
2. Virtuelle Umgebung erstellen:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Anwendung starten:
```bash
python app.py
```

### Release erstellen

1. Version in `app.py` aktualisieren
2. GitHub Release erstellen
3. ZIP-Archiv mit allen Dateien hochladen

## Sicherheit

- Service läuft als nicht-root Benutzer
- Firewall-Konfiguration über UFW
- Nginx als Reverse Proxy
- Sichere Update-Mechanismen mit Backup

## Troubleshooting

### Service startet nicht

```bash
# Logs prüfen
sudo journalctl -u devicebox -f

# Berechtigungen prüfen
ls -la /opt/devicebox/

# Service-Status
sudo systemctl status devicebox
```

### Weboberfläche nicht erreichbar

```bash
# Port prüfen
sudo netstat -tlnp | grep 8080

# Firewall prüfen
sudo ufw status

# Nginx-Status
sudo systemctl status nginx
```

### Update-Probleme

```bash
# Update-Logs prüfen
tail -f /opt/devicebox/logs/update.log

# Manueller Update-Check
python3 /opt/devicebox/update.py
```

## Lizenz

MIT License - siehe LICENSE Datei für Details.

## Beitragen

1. Fork das Repository
2. Erstelle einen Feature-Branch
3. Committe deine Änderungen
4. Push zum Branch
5. Erstelle einen Pull Request

## Support

Bei Problemen oder Fragen:
- Erstelle ein Issue auf GitHub
- Prüfe die Logs: `sudo journalctl -u devicebox -f`
- Kontaktiere den Entwickler
