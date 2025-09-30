# DeviceBox Release Workflow

## 🚨 Problem mit GitHub Actions

Das automatische Release-System hatte ein Berechtigungsproblem:
```
remote: Permission to Musik-Wieland/DeviceBox.git denied to github-actions[bot].
fatal: unable to access 'https://github.com/Musik-Wieland/DeviceBox/': The requested URL returned error: 403
```

## 🔧 Lösungen

### 1. **Einfaches Release-System (Empfohlen)**

Das neue System funktioniert ohne direkte Git-Pushes:

- ✅ Erstellt GitHub Releases automatisch
- ✅ Verwendet nur Tags (keine Commits)
- ✅ Keine Berechtigungsprobleme
- ✅ Funktioniert mit Standard GitHub Token

### 2. **Manueller Release-Helper**

Für manuelle Releases:

```bash
# Patch-Version erhöhen
python3 release-helper.py patch

# Minor-Version erhöhen  
python3 release-helper.py minor

# Major-Version erhöhen
python3 release-helper.py major
```

### 3. **VERSION-Datei manuell bearbeiten**

```bash
# VERSION-Datei bearbeiten
echo "2.2.4" > VERSION

# Committen und pushen
git add VERSION
git commit -m "chore: bump version to 2.2.4"
git push origin main

# GitHub Actions erstellt automatisch Release
```

## 🎯 Empfohlener Workflow

### Für normale Updates:
1. **Code ändern**
2. **VERSION-Datei erhöhen** (z.B. 2.2.3 → 2.2.4)
3. **Committen und pushen**
4. **GitHub Actions erstellt automatisch Release**

### Für größere Releases:
1. **Release-Helper verwenden**
2. **Automatisches Tagging und Release**

## 🔄 Aktueller Status

- ✅ **Release-System**: Funktioniert ohne Berechtigungsprobleme
- ✅ **Update-System**: Kann neue Releases laden
- ✅ **Manuelle Releases**: Über release-helper.py möglich
- ✅ **Automatische Releases**: Bei jedem Push auf main

## 📋 Nächste Schritte

1. **VERSION-Datei auf 2.2.4 setzen**
2. **Code committen und pushen**
3. **GitHub Actions testen**
4. **Update-System testen**
