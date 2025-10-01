#!/usr/bin/env python3
"""
DeviceBox Sudoers Setup
Konfiguriert sudo-Berechtigungen für den DeviceBox-Service
"""

import os
import subprocess
import sys

def setup_sudoers():
    """Konfiguriert sudo-Berechtigungen für DeviceBox-Updates"""
    
    # Service-Benutzer ermitteln
    service_user = os.getenv('SERVICE_USER', 'pi')
    
    print(f"Konfiguriere sudo-Berechtigungen für Benutzer: {service_user}")
    
    # Sudoers-Eintrag erstellen
    sudoers_entry = f"""
# DeviceBox Update-Berechtigungen für {service_user}
{service_user} ALL=(ALL) NOPASSWD: /usr/bin/python3 /opt/devicebox/update_system.py update
{service_user} ALL=(ALL) NOPASSWD: /usr/bin/python3 /opt/devicebox/update_system.py check
{service_user} ALL=(ALL) NOPASSWD: /opt/devicebox/venv/bin/python /opt/devicebox/update_system.py update
{service_user} ALL=(ALL) NOPASSWD: /opt/devicebox/venv/bin/python /opt/devicebox/update_system.py check
"""
    
    try:
        # Erstelle temporäre sudoers-Datei
        temp_file = '/tmp/devicebox_sudoers'
        with open(temp_file, 'w') as f:
            f.write(sudoers_entry.strip())
        
        # Validiere sudoers-Syntax
        result = subprocess.run(['sudo', 'visudo', '-c', '-f', temp_file], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ Sudoers-Syntax ist korrekt")
            
            # Füge Eintrag zu sudoers hinzu
            sudoers_file = f'/etc/sudoers.d/devicebox_{service_user}'
            
            # Kopiere temporäre Datei
            subprocess.run(['sudo', 'cp', temp_file, sudoers_file], check=True)
            subprocess.run(['sudo', 'chmod', '440', sudoers_file], check=True)
            
            print(f"✓ Sudoers-Eintrag erstellt: {sudoers_file}")
            print("✓ DeviceBox kann jetzt Updates über die GUI durchführen")
            
            return True
            
        else:
            print(f"✗ Sudoers-Syntax-Fehler: {result.stderr}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"✗ Fehler beim Erstellen der sudoers-Datei: {e}")
        return False
    except Exception as e:
        print(f"✗ Unerwarteter Fehler: {e}")
        return False
    finally:
        # Lösche temporäre Datei
        try:
            os.unlink(temp_file)
        except:
            pass

def test_sudo_access():
    """Testet sudo-Zugriff für DeviceBox-Updates"""
    service_user = os.getenv('SERVICE_USER', 'pi')
    
    print(f"Teste sudo-Zugriff für Benutzer: {service_user}")
    
    try:
        # Teste sudo-Zugriff
        result = subprocess.run([
            'sudo', '-u', service_user, 
            'sudo', '-n', '/usr/bin/python3', '/opt/devicebox/update_system.py', 'check'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✓ Sudo-Zugriff funktioniert")
            return True
        else:
            print(f"✗ Sudo-Zugriff fehlgeschlagen: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ Test-Fehler: {e}")
        return False

if __name__ == "__main__":
    print("=== DeviceBox Sudoers Setup ===")
    
    if os.geteuid() != 0:
        print("Dieses Skript muss als root ausgeführt werden")
        print("Führen Sie aus: sudo python3 setup_sudoers.py")
        sys.exit(1)
    
    success = setup_sudoers()
    
    if success:
        print("\n=== Teste Konfiguration ===")
        test_sudo_access()
        
        print("\n=== Setup abgeschlossen ===")
        print("DeviceBox kann jetzt Updates über die GUI durchführen")
    else:
        print("\n=== Setup fehlgeschlagen ===")
        print("Manuelle Konfiguration erforderlich")
        sys.exit(1)
