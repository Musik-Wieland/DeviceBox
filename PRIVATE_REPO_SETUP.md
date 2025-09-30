# Private Repository Setup für DeviceBox

## 🔒 GitHub Personal Access Token erstellen

### 1. Token generieren
1. Gehe zu GitHub → **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. Klicke **"Generate new token"** → **"Generate new token (classic)"**
3. Gib einen Namen ein: `DeviceBox Updates`
4. Wähle die Scopes:
   - ✅ **`repo`** (Full control of private repositories)
   - ✅ **`read:org`** (Read org and team membership)
5. Klicke **"Generate token"**
6. **Kopiere den Token** (wird nur einmal angezeigt!)

### 2. Token auf Raspberry Pi setzen

#### Option A: Umgebungsvariable setzen
```bash
# Temporär (nur für aktuelle Session)
export GITHUB_TOKEN="ghp_your_token_here"

# Permanently in ~/.bashrc
echo 'export GITHUB_TOKEN="ghp_your_token_here"' >> ~/.bashrc
source ~/.bashrc
```

#### Option B: Systemd Service mit Token
```bash
# Service-Datei bearbeiten
sudo nano /etc/systemd/system/devicebox.service

# Environment-Variable hinzufügen:
[Service]
Environment=GITHUB_TOKEN=ghp_your_token_here
```

#### Option C: Konfigurationsdatei
```bash
# Token in config.json speichern
nano /home/pi/devicebox/config.json

# Hinzufügen:
{
  "github": {
    "token": "ghp_your_token_here"
  }
}
```

## 🚀 Installation mit privatem Repository

### Einzeiler Installation mit Token
```bash
GITHUB_TOKEN="ghp_your_token_here" curl -sSL https://raw.githubusercontent.com/yourusername/devicebox/main/install.sh | bash
```

### Manuelle Installation
```bash
# Token setzen
export GITHUB_TOKEN="ghp_your_token_here"

# Installation ausführen
./install.sh
```

## 🔧 Repository-URL anpassen

### In update_manager.py
```python
# Zeile 17 ändern:
self.repo_url = "https://github.com/DEIN_USERNAME/devicebox.git"
```

### In install.sh
```bash
# Zeile 122 und 131 ändern:
git clone https://${GITHUB_TOKEN}@github.com/DEIN_USERNAME/devicebox.git .
```

## 🛡️ Sicherheitshinweise

### Token-Sicherheit
- **Niemals** den Token in öffentlichen Repositories committen
- Token regelmäßig **rotieren** (alle 90 Tage)
- **Minimale Berechtigungen** vergeben
- Token bei Kompromittierung **sofort widerrufen**

### Sichere Speicherung
```bash
# Token-Datei mit eingeschränkten Berechtigungen
chmod 600 ~/.github_token
echo "ghp_your_token_here" > ~/.github_token
export GITHUB_TOKEN=$(cat ~/.github_token)
```

## 🔍 Troubleshooting

### Token-Probleme
```bash
# Token testen
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user

# Repository-Zugriff testen
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/repos/yourusername/devicebox
```

### Update-Fehler
```bash
# Logs prüfen
sudo journalctl -u devicebox -f

# Manueller Update-Test
python3 -c "
import os
os.environ['GITHUB_TOKEN'] = 'ghp_your_token_here'
from update_manager import UpdateManager
print(UpdateManager().check_for_updates())
"
```

## 📝 Beispiel-Konfiguration

### Vollständige config.json
```json
{
  "app": {
    "name": "DeviceBox",
    "version": "1.0.0",
    "debug": false,
    "host": "0.0.0.0",
    "port": 5000
  },
  "github": {
    "token": "ghp_your_token_here",
    "repo": "yourusername/devicebox"
  },
  "update": {
    "check_interval": 3600,
    "auto_update": false,
    "backup_enabled": true
  }
}
```

---

**Wichtig:** Ersetze `yourusername` und `ghp_your_token_here` mit deinen echten Werten!
