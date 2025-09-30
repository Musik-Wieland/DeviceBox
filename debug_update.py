#!/usr/bin/env python3
"""
DeviceBox Update Debug-Skript
Testet das Update-System und zeigt detaillierte Informationen
"""

import os
import sys
import json

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("Warnung: requests-Modul nicht verfügbar")

try:
    from auto_update import DeviceBoxAutoUpdater
    HAS_AUTO_UPDATE = True
except ImportError as e:
    HAS_AUTO_UPDATE = False
    print(f"Warnung: auto_update-Modul nicht verfügbar: {e}")

def debug_update_system():
    """Debug-Funktion für das Update-System"""
    print("=== DeviceBox Update Debug ===\n")
    
    if not HAS_AUTO_UPDATE:
        print("Fehler: auto_update-Modul nicht verfügbar")
        return
    
    # Initialisiere Updater
    updater = DeviceBoxAutoUpdater()
    
    # 1. Prüfe aktuelle Version
    print("1. Aktuelle Version:")
    current_version = updater.get_current_version()
    print(f"   Aktuelle Version: {current_version}")
    
    # 2. Prüfe Version-Datei
    print("\n2. Version-Datei:")
    if os.path.exists(updater.version_file):
        try:
            with open(updater.version_file, 'r') as f:
                version_data = json.load(f)
            print(f"   Version-Datei gefunden: {updater.version_file}")
            print(f"   Gespeicherte Version: {version_data.get('version', 'N/A')}")
            print(f"   Gespeicherter Commit: {version_data.get('commit_hash', 'N/A')}")
            print(f"   Letzte Aktualisierung: {version_data.get('updated_at', 'N/A')}")
        except Exception as e:
            print(f"   Fehler beim Lesen der Version-Datei: {e}")
    else:
        print(f"   Version-Datei nicht gefunden: {updater.version_file}")
    
    # 3. Prüfe GitHub-Verbindung
    print("\n3. GitHub-Verbindung:")
    try:
        commit_hash, commit_message = updater.get_latest_commit_hash()
        print(f"   Verbindung erfolgreich")
        print(f"   Neuester Commit: {commit_hash}")
        print(f"   Commit-Nachricht: {commit_message}")
    except Exception as e:
        print(f"   Fehler bei GitHub-Verbindung: {e}")
        return
    
    # 4. Prüfe auf Updates
    print("\n4. Update-Check:")
    try:
        update_info = updater.check_for_updates()
        print(f"   Update verfügbar: {update_info.get('available', False)}")
        print(f"   Aktuelle Version: {update_info.get('current_version', 'N/A')}")
        print(f"   Neueste Version: {update_info.get('latest_version', 'N/A')}")
        print(f"   Nachricht: {update_info.get('message', 'N/A')}")
        
        if 'error' in update_info:
            print(f"   Fehler: {update_info['error']}")
    except Exception as e:
        print(f"   Fehler beim Update-Check: {e}")
    
    # 5. Prüfe verfügbare USB-Geräte
    print("\n5. Verfügbare USB-Geräte:")
    try:
        devices = updater.get_available_usb_devices()
        print(f"   {len(devices)} Geräte gefunden:")
        for i, device in enumerate(devices[:5]):  # Zeige nur erste 5
            print(f"   {i+1}. {device.get('description', 'Unbekannt')}")
            if device.get('type') == 'usb':
                print(f"      USB: {device.get('vendor_product', 'N/A')}")
            else:
                print(f"      Seriell: {device.get('port', 'N/A')}")
    except Exception as e:
        print(f"   Fehler beim Ermitteln der USB-Geräte: {e}")
    
    # 6. Prüfe Installationsverzeichnis
    print("\n6. Installationsverzeichnis:")
    install_dir = updater.install_dir
    print(f"   Installationsverzeichnis: {install_dir}")
    print(f"   Existiert: {os.path.exists(install_dir)}")
    
    if os.path.exists(install_dir):
        files = os.listdir(install_dir)
        print(f"   Dateien im Verzeichnis: {len(files)}")
        important_files = ['app.py', 'auto_update.py', 'device_manager.py', 'requirements.txt']
        for file in important_files:
            exists = os.path.exists(os.path.join(install_dir, file))
            print(f"   {file}: {'✓' if exists else '✗'}")
    
    # 7. Prüfe Berechtigungen
    print("\n7. Berechtigungen:")
    try:
        import pwd
        current_user = pwd.getpwuid(os.getuid()).pw_name
        print(f"   Aktueller Benutzer: {current_user}")
        
        if os.path.exists(install_dir):
            stat_info = os.stat(install_dir)
            owner = pwd.getpwuid(stat_info.st_uid).pw_name
            print(f"   Besitzer des Installationsverzeichnisses: {owner}")
    except Exception as e:
        print(f"   Fehler beim Prüfen der Berechtigungen: {e}")
    
    print("\n=== Debug abgeschlossen ===")

def test_update_check():
    """Testet nur den Update-Check"""
    print("=== Update-Check Test ===\n")
    
    updater = DeviceBoxAutoUpdater()
    
    try:
        result = updater.check_for_updates()
        print("Update-Check Ergebnis:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Fehler beim Update-Check: {e}")
        import traceback
        traceback.print_exc()

def test_github_connection():
    """Testet nur die GitHub-Verbindung"""
    print("=== GitHub-Verbindung Test ===\n")
    
    updater = DeviceBoxAutoUpdater()
    
    try:
        commit_hash, commit_message = updater.get_latest_commit_hash()
        print(f"GitHub-Verbindung erfolgreich!")
        print(f"Commit-Hash: {commit_hash}")
        print(f"Commit-Nachricht: {commit_message}")
    except Exception as e:
        print(f"GitHub-Verbindung fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'check':
            test_update_check()
        elif sys.argv[1] == 'github':
            test_github_connection()
        else:
            print("Verwendung: python debug_update.py [check|github]")
    else:
        debug_update_system()
