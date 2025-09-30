# DeviceBox Update-Guide

## Update-Systeme

DeviceBox bietet mehrere Update-Methoden:

### 1. Auto-Update-System (Empfohlen)
Das robuste Auto-Update-System lädt Updates direkt vom GitHub-Repository herunter.

```bash
# Auto-Update ausführen
sudo python3 /opt/devicebox/auto_update.py

# Nur Update-Check
sudo python3 /opt/devicebox/auto_update.py check
```

### 2. Einfaches Update-Skript
Ein benutzerfreundliches Update-Skript mit besserer Ausgabe.

```bash
# Einfaches Update
sudo python3 /opt/devicebox/update_simple.py
```

### 3. Release-basiertes Update
Das klassische Update-System für GitHub-Releases (falls verfügbar).

```bash
# Release-basiertes Update
sudo python3 /opt/devicebox/update.py
```

### 4. Installationsskript-Update
Das Installationsskript erkennt automatisch bestehende Installationen.

```bash
# Interaktives Update
curl -fsSL https://raw.githubusercontent.com/Musik-Wieland/DeviceBox/main/install.sh | bash

# Automatisches Update
curl -fsSL https://raw.githubusercontent.com/Musik-Wieland/DeviceBox/main/install.sh | bash -s -- --force-update
```

## Update-Features

### ✅ Sicherheitsfeatures
- **Automatische Backups** vor jedem Update
- **Rollback-Funktion** bei Fehlern
- **Datenverlust-Schutz** für Konfigurationen
- **Service-Management** (automatisches Stoppen/Starten)

### ✅ Robuste Fehlerbehandlung
- **Timeout-Schutz** verhindert hängende Updates
- **Fallback-Systeme** bei verschiedenen Fehlern
- **Detaillierte Logs** für Debugging
- **Automatische Wiederherstellung** bei Fehlern

## Häufige Probleme

### Problem: "list index out of range"
**Ursache:** Keine GitHub-Releases verfügbar
**Lösung:** Verwende das Auto-Update-System:
```bash
sudo python3 /opt/devicebox/auto_update.py
```

### Problem: "Keine Release-Assets verfügbar"
**Ursache:** Repository hat noch keine Releases
**Lösung:** Verwende das Auto-Update-System oder das Installationsskript

### Problem: Update-Timeout
**Ursache:** Langsame Internetverbindung oder GitHub-Probleme
**Lösung:** 
```bash
# Erhöhe Timeout oder verwende lokales Update
sudo python3 /opt/devicebox/update_simple.py
```

## Debug-Tools

### Debug-Skript
```bash
# Vollständiges System-Debug
sudo python3 /opt/devicebox/debug_update.py

# Nur Update-Check
sudo python3 /opt/devicebox/debug_update.py check

# Nur GitHub-Verbindung
sudo python3 /opt/devicebox/debug_update.py github
```

### Test-Skript
```bash
# Einfacher Update-Test
sudo python3 /opt/devicebox/test_update.py
```

## Service-Management

### Service-Status prüfen
```bash
sudo systemctl status devicebox
```

### Service neu starten
```bash
sudo systemctl restart devicebox
```

### Service-Logs anzeigen
```bash
# Live-Logs
sudo journalctl -u devicebox -f

# Letzte Logs
sudo journalctl -u devicebox --since "1 hour ago"
```

## Empfohlene Update-Strategie

1. **Für normale Updates:** Verwende das Auto-Update-System
2. **Für Debugging:** Verwende das Debug-Skript
3. **Für Neuinstallationen:** Verwende das Installationsskript
4. **Für automatische Updates:** Aktiviere Auto-Update in der Web-Oberfläche

## Update-Befehle Übersicht

| Befehl | Beschreibung | Empfehlung |
|--------|--------------|------------|
| `auto_update.py` | Robuste Auto-Updates | ⭐ Empfohlen |
| `update_simple.py` | Benutzerfreundliches Update | ✅ Gut |
| `update.py` | Release-basiertes Update | ⚠️ Nur bei Releases |
| `install.sh` | Vollständige Installation/Update | ✅ Für Neuinstallationen |
| `debug_update.py` | Debug-Informationen | 🔧 Für Probleme |

## Support

Bei Update-Problemen:
1. Führe das Debug-Skript aus
2. Prüfe die Service-Logs
3. Verwende das Auto-Update-System als Fallback
4. Bei anhaltenden Problemen: Neuinstallation mit dem Installationsskript
