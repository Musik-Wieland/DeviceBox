#!/usr/bin/env python3
"""
DeviceBox Einfaches Update-Skript
Verwendet das Auto-Update-System als Standard
"""

import os
import sys
import subprocess

def main():
    """Hauptfunktion für einfaches Update"""
    print("DeviceBox Update-System")
    print("=" * 30)
    
    # Bestimme Installationsverzeichnis
    install_dir = os.getenv('INSTALL_DIR', '/opt/devicebox')
    auto_update_script = os.path.join(install_dir, 'auto_update.py')
    
    # Prüfe ob Auto-Update-Skript existiert
    if not os.path.exists(auto_update_script):
        print(f"Fehler: Auto-Update-Skript nicht gefunden: {auto_update_script}")
        print("Bitte führen Sie das Installationsskript erneut aus.")
        return 1
    
    print(f"Verwende Auto-Update-System: {auto_update_script}")
    print()
    
    try:
        # Führe Auto-Update aus
        result = subprocess.run([sys.executable, auto_update_script], 
                              capture_output=True, text=True, timeout=300)
        
        # Zeige Ausgabe
        if result.stdout:
            print("Update-Ausgabe:")
            print(result.stdout)
        
        if result.stderr:
            print("Update-Fehler:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("\n✅ Update erfolgreich abgeschlossen!")
            return 0
        else:
            print(f"\n❌ Update fehlgeschlagen (Exit-Code: {result.returncode})")
            return 1
            
    except subprocess.TimeoutExpired:
        print("\n❌ Update-Timeout: Das Update dauerte zu lange")
        return 1
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
