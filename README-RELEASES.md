# DeviceBox Automatisches Release-System

## 🚀 Übersicht

DeviceBox verwendet ein automatisches Release-System, das bei jedem Push auf den `main` Branch automatisch eine neue Version erstellt.

## 📋 Funktionsweise

### Automatische Releases
- **Trigger**: Jeder Push auf `main` Branch
- **Versionierung**: Automatisches Patch-Increment (z.B. 2.2.0 → 2.2.1)
- **GitHub Actions**: Erstellt automatisch GitHub Releases
- **Update-System**: Neue Versionen sind sofort verfügbar

### Workflow
1. **Code Push** → GitHub Actions startet
2. **Version Check** → Prüft ob neue Version nötig
3. **Version Bump** → Erhöht Patch-Version
4. **Git Tag** → Erstellt Version-Tag
5. **GitHub Release** → Erstellt Release mit Assets
6. **Update verfügbar** → Update-System kann neue Version laden

## 🛠️ Manuelle Releases

### Release Helper Script
```bash
# Patch-Version erhöhen (2.2.0 → 2.2.1)
python3 release-helper.py patch

# Minor-Version erhöhen (2.2.0 → 2.3.0)
python3 release-helper.py minor

# Major-Version erhöhen (2.2.0 → 3.0.0)
python3 release-helper.py major
```

### Was passiert beim manuellen Release:
1. **VERSION-Datei** wird aktualisiert
2. **version.json** wird aktualisiert
3. **Git Tag** wird erstellt
4. **Änderungen** werden committed und gepusht
5. **GitHub Actions** erstellt automatisch das Release

## 📁 Dateien

### VERSION
```
2.2.0
```
- Enthält die aktuelle Versionsnummer
- Wird automatisch erhöht

### version.json
```json
{
  "version": "2.2.0",
  "build_date": "2025-09-30T17:00:00Z",
  "commit": "abc12345",
  "branch": "main"
}
```
- Metadaten für das Update-System
- Wird automatisch aktualisiert

### .github/workflows/auto-release.yml
- GitHub Actions Workflow
- Automatische Release-Erstellung
- Läuft bei jedem Push auf `main`

## 🔄 Update-System Integration

Das Update-System (`update_system.py`) nutzt die GitHub Releases:

```python
# Prüft auf neue Releases
latest_release = get_latest_release()

# Lädt neueste Version herunter
download_url = latest_release['zipball_url']

# Installiert Update
install_update(extracted_dir)
```

## 🎯 Vorteile

### Für Entwickler:
- ✅ **Automatisch**: Keine manuellen Releases nötig
- ✅ **Konsistent**: Einheitliche Versionierung
- ✅ **Schnell**: Sofort verfügbare Updates
- ✅ **Sicher**: Automatische Tests vor Release

### Für Benutzer:
- ✅ **Einfach**: Ein-Klick Updates
- ✅ **Sicher**: Automatische Backups
- ✅ **Schnell**: Direkte GitHub-Downloads
- ✅ **Zuverlässig**: Getestete Releases

## 🚨 Wichtige Hinweise

### Versionierung:
- **Patch** (2.2.0 → 2.2.1): Bugfixes, kleine Verbesserungen
- **Minor** (2.2.0 → 2.3.0): Neue Features, größere Änderungen
- **Major** (2.2.0 → 3.0.0): Breaking Changes, große Umstrukturierungen

### Release-Regeln:
- Jeder Push auf `main` erstellt automatisch ein Release
- Duplikate werden automatisch erkannt und vermieden
- Releases enthalten immer alle Projektdateien
- Update-System kann sofort neue Versionen laden

## 🔧 Troubleshooting

### Release wird nicht erstellt:
```bash
# GitHub Actions Status prüfen
# Repository → Actions → Auto Release

# Manuell triggern
python3 release-helper.py patch
```

### Update-System findet keine neue Version:
```bash
# Version prüfen
cat VERSION

# GitHub Release prüfen
curl -s https://api.github.com/repos/Musik-Wieland/DeviceBox/releases/latest
```

### Git Tag Probleme:
```bash
# Alle Tags anzeigen
git tag -l

# Tag löschen (falls nötig)
git tag -d v2.2.1
git push origin :refs/tags/v2.2.1
```

## 📞 Support

Bei Problemen mit dem Release-System:
1. GitHub Actions Logs prüfen
2. VERSION-Datei überprüfen
3. Git Status prüfen
4. Manuelles Release versuchen
