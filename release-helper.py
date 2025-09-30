#!/usr/bin/env python3
"""
DeviceBox Release Helper
Hilft beim manuellen Erstellen von Releases
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from packaging import version

def get_current_version():
    """Aktuelle Version aus VERSION-Datei lesen"""
    try:
        with open('VERSION', 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return '1.0.0'

def bump_version(current_version, bump_type='patch'):
    """Version erhöhen"""
    v = version.parse(current_version)
    
    if bump_type == 'major':
        return f"{v.major + 1}.0.0"
    elif bump_type == 'minor':
        return f"{v.major}.{v.minor + 1}.0"
    elif bump_type == 'patch':
        return f"{v.major}.{v.minor}.{v.micro + 1}"
    else:
        raise ValueError(f"Unbekannter Bump-Typ: {bump_type}")

def update_version_file(new_version):
    """VERSION-Datei aktualisieren"""
    with open('VERSION', 'w') as f:
        f.write(new_version)
    print(f"✅ VERSION-Datei aktualisiert: {new_version}")

def update_version_json(new_version):
    """version.json aktualisieren"""
    version_data = {
        "version": new_version,
        "build_date": datetime.utcnow().isoformat() + "Z",
        "commit": get_git_commit(),
        "branch": get_git_branch()
    }
    
    with open('version.json', 'w') as f:
        json.dump(version_data, f, indent=2)
    print(f"✅ version.json aktualisiert: {new_version}")

def get_git_commit():
    """Git Commit Hash abrufen"""
    try:
        result = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True)
        return result.stdout.strip()[:8]
    except:
        return "unknown"

def get_git_branch():
    """Git Branch abrufen"""
    try:
        result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], capture_output=True, text=True)
        return result.stdout.strip()
    except:
        return "unknown"

def create_git_tag(new_version):
    """Git Tag erstellen"""
    tag_name = f"v{new_version}"
    
    try:
        # Prüfe ob Tag bereits existiert
        result = subprocess.run(['git', 'tag', '-l', tag_name], capture_output=True, text=True)
        if tag_name in result.stdout:
            print(f"⚠️  Tag {tag_name} existiert bereits!")
            return False
        
        # Tag erstellen
        subprocess.run(['git', 'tag', tag_name], check=True)
        print(f"✅ Git Tag erstellt: {tag_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Fehler beim Erstellen des Git Tags: {e}")
        return False

def commit_changes(new_version):
    """Änderungen committen"""
    try:
        subprocess.run(['git', 'add', 'VERSION', 'version.json'], check=True)
        subprocess.run(['git', 'commit', '-m', f'chore: bump version to {new_version}'], check=True)
        print(f"✅ Änderungen committed: {new_version}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Fehler beim Committen: {e}")
        return False

def push_changes():
    """Änderungen pushen"""
    try:
        subprocess.run(['git', 'push', 'origin', 'main'], check=True)
        subprocess.run(['git', 'push', 'origin', '--tags'], check=True)
        print("✅ Änderungen gepusht")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Fehler beim Pushen: {e}")
        return False

def main():
    """Hauptfunktion"""
    if len(sys.argv) < 2:
        print("Verwendung: python3 release-helper.py [patch|minor|major]")
        print("Beispiele:")
        print("  python3 release-helper.py patch   # 1.0.0 → 1.0.1")
        print("  python3 release-helper.py minor   # 1.0.0 → 1.1.0")
        print("  python3 release-helper.py major   # 1.0.0 → 2.0.0")
        sys.exit(1)
    
    bump_type = sys.argv[1]
    if bump_type not in ['patch', 'minor', 'major']:
        print(f"❌ Unbekannter Bump-Typ: {bump_type}")
        print("Verwende: patch, minor oder major")
        sys.exit(1)
    
    current_version = get_current_version()
    new_version = bump_version(current_version, bump_type)
    
    print(f"🔄 Version erhöhen: {current_version} → {new_version}")
    
    # Dateien aktualisieren
    update_version_file(new_version)
    update_version_json(new_version)
    
    # Git Tag erstellen
    if not create_git_tag(new_version):
        sys.exit(1)
    
    # Änderungen committen
    if not commit_changes(new_version):
        sys.exit(1)
    
    # Pushen
    if not push_changes():
        sys.exit(1)
    
    print(f"\n🎉 Release {new_version} erfolgreich erstellt!")
    print(f"🔗 GitHub wird automatisch ein Release erstellen")
    print(f"📦 Update-System kann jetzt die neue Version herunterladen")

if __name__ == '__main__':
    main()
