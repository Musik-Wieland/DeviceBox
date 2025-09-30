#!/usr/bin/env python3
"""
DeviceBox Update System
Einfaches Release-basiertes Update-System
"""

import os
import sys
import json
import requests
import tempfile
import subprocess
import shutil
from datetime import datetime

class DeviceBoxUpdater:
    def __init__(self):
        self.github_repo = "Musik-Wieland/DeviceBox"
        self.install_dir = "/opt/devicebox"
        self.version_file = os.path.join(self.install_dir, "version.json")
        self.config_file = os.path.join(self.install_dir, "config.json")
        self.data_dir = os.path.join(self.install_dir, "data")
        
    def get_current_version(self):
        """Holt die aktuelle Version"""
        try:
            if os.path.exists(self.version_file):
                with open(self.version_file, 'r') as f:
                    version_data = json.load(f)
                    return version_data.get('version', '1.0.0')
            return '1.0.0'
        except Exception as e:
            print(f"Fehler beim Lesen der Version: {e}")
            return '1.0.0'
    
    def get_latest_release(self):
        """Holt die neueste Release-Information von GitHub"""
        try:
            # Versuche zuerst die API
            url = f"https://api.github.com/repos/{self.github_repo}/releases/latest"
            headers = {
                'User-Agent': 'DeviceBox-Updater/1.0',
                'Accept': 'application/vnd.github.v3+json'
            }
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            elif response.status_code == 403:
                return self.get_latest_release_fallback()
            else:
                return self.get_latest_release_fallback()
                
        except Exception as e:
            return self.get_latest_release_fallback()
    
    def get_latest_release_fallback(self):
        """Fallback-Methode ohne GitHub API"""
        try:
            # Versuche die Releases-Seite direkt zu parsen
            url = f"https://github.com/{self.github_repo}/releases/latest"
            headers = {
                'User-Agent': 'DeviceBox-Updater/1.0'
            }
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Einfache Version aus der URL extrahieren
                # Die URL ist normalerweise: https://github.com/user/repo/releases/tag/v1.0.0
                import re
                version_match = re.search(r'/releases/tag/v?([0-9.]+)', response.url)
                if version_match:
                    version = version_match.group(1)
                    return {
                        'tag_name': f'v{version}',
                        'name': f'Release {version}',
                        'assets': [{
                            'browser_download_url': f'https://github.com/{self.github_repo}/archive/refs/tags/v{version}.zip'
                        }]
                    }
            
            return None
            
        except Exception as e:
            return None
    
    def check_for_updates(self):
        """Prüft auf verfügbare Updates"""
        try:
            # Aktuelle Version
            current_version = self.get_current_version()
            
            # Neueste Release
            latest_release = self.get_latest_release()
            if not latest_release:
                return {
                    'update_available': False,
                    'current_version': current_version,
                    'latest_version': current_version,
                    'message': 'Keine Releases verfügbar'
                }
            
            latest_version = latest_release['tag_name'].lstrip('v')
            
            # Version vergleichen
            if self.compare_versions(current_version, latest_version) < 0:
                return {
                    'update_available': True,
                    'current_version': current_version,
                    'latest_version': latest_version,
                    'release_info': latest_release,
                    'message': f'Update verfügbar: {current_version} → {latest_version}'
                }
            else:
                return {
                    'update_available': False,
                    'current_version': current_version,
                    'latest_version': latest_version,
                    'message': 'System ist bereits aktuell'
                }
                
        except Exception as e:
            return {
                'update_available': False,
                'current_version': self.get_current_version(),
                'latest_version': self.get_current_version(),
                'message': f'Fehler beim Update-Check: {e}'
            }
    
    def compare_versions(self, version1, version2):
        """Vergleicht zwei Versionen (semantic versioning)"""
        def version_tuple(v):
            return tuple(map(int, v.split('.')))
        
        try:
            v1 = version_tuple(version1)
            v2 = version_tuple(version2)
            if v1 < v2:
                return -1
            elif v1 > v2:
                return 1
            else:
                return 0
        except:
            # Fallback: String-Vergleich
            if version1 < version2:
                return -1
            elif version1 > version2:
                return 1
            else:
                return 0
    
    def download_release(self, download_url, temp_dir):
        """Lädt das Release herunter"""
        try:
            print(f"Lade Update herunter: {download_url}")
            response = requests.get(download_url, timeout=60)
            response.raise_for_status()
            
            zip_path = os.path.join(temp_dir, "update.zip")
            with open(zip_path, 'wb') as f:
                f.write(response.content)
            
            print(f"Update heruntergeladen: {zip_path}")
            return zip_path
            
        except Exception as e:
            print(f"Fehler beim Herunterladen: {e}")
            raise
    
    def extract_update(self, zip_path, temp_dir):
        """Extrahiert das Update"""
        try:
            import zipfile
            
            extracted_dir = os.path.join(temp_dir, "extracted")
            os.makedirs(extracted_dir, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extracted_dir)
            
            # Finde das Hauptverzeichnis
            contents = os.listdir(extracted_dir)
            if len(contents) == 1 and os.path.isdir(os.path.join(extracted_dir, contents[0])):
                extracted_dir = os.path.join(extracted_dir, contents[0])
            
            print(f"Update extrahiert nach: {extracted_dir}")
            return extracted_dir
            
        except Exception as e:
            print(f"Fehler beim Extrahieren: {e}")
            raise
    
    def backup_data(self):
        """Erstellt ein Backup der wichtigen Daten"""
        try:
            backup_dir = f"{self.install_dir}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            print(f"Erstelle Backup: {backup_dir}")
            
            # Erstelle Backup-Verzeichnis
            os.makedirs(backup_dir, exist_ok=True)
            
            # Backup wichtige Dateien
            if os.path.exists(self.data_dir):
                shutil.copytree(self.data_dir, os.path.join(backup_dir, "data"))
            
            if os.path.exists(self.config_file):
                shutil.copy2(self.config_file, backup_dir)
            
            if os.path.exists(self.version_file):
                shutil.copy2(self.version_file, backup_dir)
            
            print("Backup erfolgreich erstellt")
            return backup_dir
            
        except Exception as e:
            print(f"Warnung beim Backup: {e}")
            return None
    
    def install_update(self, extracted_dir):
        """Installiert das Update"""
        old_install_dir = None
        try:
            print("Installiere Update...")
            
            # Prüfe ob wir auf einem Raspberry Pi sind (systemctl verfügbar)
            is_raspberry_pi = os.path.exists('/etc/os-release') and 'raspbian' in open('/etc/os-release').read().lower()
            
            if is_raspberry_pi:
                # Stoppe den Service nur auf Raspberry Pi
                print("Stoppe DeviceBox Service...")
                subprocess.run(['sudo', 'systemctl', 'stop', 'devicebox'], check=True)
            
            # Erstelle temporäres Verzeichnis für alte Installation
            old_install_dir = f"{self.install_dir}_old"
            if os.path.exists(old_install_dir):
                shutil.rmtree(old_install_dir)
            
            # Verschiebe aktuelle Installation
            if os.path.exists(self.install_dir):
                print(f"Verschiebe aktuelle Installation nach: {old_install_dir}")
                shutil.move(self.install_dir, old_install_dir)
            
            # Kopiere neue Version
            print(f"Kopiere neue Version nach: {self.install_dir}")
            
            # Kopiere alle Dateien aus dem extrahierten Verzeichnis
            for item in os.listdir(extracted_dir):
                src = os.path.join(extracted_dir, item)
                dst = os.path.join(self.install_dir, item)
                
                if os.path.isdir(src):
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
            
            # Stelle wichtige Dateien wieder her
            self.restore_data(old_install_dir)
            
            # Setze Berechtigungen nur auf Raspberry Pi
            if is_raspberry_pi:
                service_user = os.getenv('SERVICE_USER', 'pi')
                print(f"Setze Berechtigungen für Benutzer: {service_user}")
                subprocess.run(['sudo', 'chown', '-R', f'{service_user}:{service_user}', self.install_dir], check=True)
                
                # Setze ausführbare Berechtigungen
                executable_files = ['app.py', 'update.py', 'device_manager.py']
                for file in executable_files:
                    file_path = os.path.join(self.install_dir, file)
                    if os.path.exists(file_path):
                        subprocess.run(['sudo', 'chmod', '+x', file_path], check=True)
            
            # Aktualisiere Version
            self.update_version_file()
            
            if is_raspberry_pi:
                # Starte Service neu nur auf Raspberry Pi
                print("Starte DeviceBox Service neu...")
                subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=True)
                subprocess.run(['sudo', 'systemctl', 'start', 'devicebox'], check=True)
                
                # Prüfe Service-Status
                import time
                time.sleep(3)
                result = subprocess.run(['sudo', 'systemctl', 'is-active', 'devicebox'], capture_output=True, text=True)
                if result.returncode == 0 and 'active' in result.stdout:
                    print("Service läuft erfolgreich")
                else:
                    raise Exception("Service konnte nicht gestartet werden")
            
            # Entferne alte Installation nach erfolgreichem Update
            if old_install_dir and os.path.exists(old_install_dir):
                print(f"Entferne alte Installation: {old_install_dir}")
                shutil.rmtree(old_install_dir)
            
            print("Update erfolgreich installiert!")
            return True
                
        except Exception as e:
            print(f"Fehler bei der Installation: {e}")
            
            # Bei Fehler: Stelle alte Installation wieder her
            try:
                if old_install_dir and os.path.exists(old_install_dir):
                    print("Stelle alte Installation wieder her...")
                    if os.path.exists(self.install_dir):
                        shutil.rmtree(self.install_dir)
                    shutil.move(old_install_dir, self.install_dir)
                    
                    if is_raspberry_pi:
                        subprocess.run(['sudo', 'systemctl', 'start', 'devicebox'], check=False)
                    print("Alte Installation wiederhergestellt")
            except Exception as restore_error:
                print(f"Fehler beim Wiederherstellen: {restore_error}")
            
            raise Exception(f"Fehler bei der Installation: {e}")
    
    def restore_data(self, old_install_dir):
        """Stellt wichtige Daten aus der alten Installation wieder her"""
        try:
            # Stelle nur wichtige Daten wieder her, NICHT die gesamte Installation
            
            # 1. Datenverzeichnis (Gerätekonfigurationen, etc.)
            old_data_dir = os.path.join(old_install_dir, 'data')
            if os.path.exists(old_data_dir):
                if os.path.exists(self.data_dir):
                    shutil.rmtree(self.data_dir)
                shutil.copytree(old_data_dir, self.data_dir)
                print("Datenverzeichnis wiederhergestellt")
            
            # 2. Konfigurationsdateien (nur spezifische)
            config_files = ['config.json', 'devices.json']
            for config_file in config_files:
                old_config = os.path.join(old_install_dir, config_file)
                if os.path.exists(old_config):
                    new_config = os.path.join(self.install_dir, config_file)
                    shutil.copy2(old_config, new_config)
                    print(f"Konfigurationsdatei {config_file} wiederhergestellt")
            
            # 3. Logs-Verzeichnis
            old_logs_dir = os.path.join(old_install_dir, 'logs')
            if os.path.exists(old_logs_dir):
                new_logs_dir = os.path.join(self.install_dir, 'logs')
                if not os.path.exists(new_logs_dir):
                    os.makedirs(new_logs_dir)
                # Kopiere nur neue Logs, nicht alle
                for log_file in os.listdir(old_logs_dir):
                    if log_file.endswith('.log'):
                        shutil.copy2(os.path.join(old_logs_dir, log_file), 
                                   os.path.join(new_logs_dir, log_file))
                print("Logs wiederhergestellt")
            
            # 4. Virtuelle Umgebung (falls vorhanden)
            old_venv = os.path.join(old_install_dir, 'venv')
            if os.path.exists(old_venv):
                new_venv = os.path.join(self.install_dir, 'venv')
                if os.path.exists(new_venv):
                    shutil.rmtree(new_venv)
                shutil.copytree(old_venv, new_venv)
                print("Virtuelle Umgebung wiederhergestellt")
            
            print("Wichtige Daten erfolgreich wiederhergestellt")
        except Exception as e:
            print(f"Warnung beim Wiederherstellen der Daten: {e}")
    
    def update_version_file(self):
        """Aktualisiert die Versionsdatei"""
        try:
            version_data = {
                'version': '1.0.0',  # Wird durch das Release überschrieben
                'updated_at': datetime.now().isoformat(),
                'update_method': 'release'
            }
            
            with open(self.version_file, 'w') as f:
                json.dump(version_data, f, indent=2)
            
            print("Versionsdatei aktualisiert")
        except Exception as e:
            print(f"Fehler beim Aktualisieren der Versionsdatei: {e}")
    
    def update(self):
        """Führt das komplette Update durch"""
        try:
            print("DeviceBox Update gestartet...")
            
            # Prüfe auf Updates
            update_info = self.check_for_updates()
            if not update_info['update_available']:
                print(update_info['message'])
                return True
            
            print(f"Update verfügbar: {update_info['message']}")
            
            # Hole Release-Informationen
            release_info = update_info['release_info']
            
            # Prüfe ob Assets vorhanden sind, falls nicht verwende zipball_url
            if not release_info.get('assets') or len(release_info['assets']) == 0:
                # Verwende zipball_url als Fallback
                download_url = release_info.get('zipball_url')
                if not download_url:
                    raise Exception("Keine Release-Assets oder zipball_url verfügbar")
            else:
                download_url = release_info['assets'][0]['browser_download_url']
            
            # Erstelle temporäres Verzeichnis
            with tempfile.TemporaryDirectory() as temp_dir:
                # Backup erstellen
                self.backup_data()
                
                # Update herunterladen
                zip_path = self.download_release(download_url, temp_dir)
                
                # Update extrahieren
                extracted_dir = self.extract_update(zip_path, temp_dir)
                
                # Update installieren
                self.install_update(extracted_dir)
            
            print("Update erfolgreich abgeschlossen!")
            return True
            
        except Exception as e:
            print(f"Update fehlgeschlagen: {e}")
            return False

def main():
    """Hauptfunktion"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        updater = DeviceBoxUpdater()
        
        if command == "check":
            # Nur prüfen - nur JSON ausgeben
            update_info = updater.check_for_updates()
            print(json.dumps(update_info, indent=2))
            
        elif command == "update":
            # Update durchführen
            success = updater.update()
            sys.exit(0 if success else 1)
            
        else:
            print(json.dumps({'error': 'Unbekannter Befehl. Verfügbare Befehle: check, update'}, indent=2))
            sys.exit(1)
    else:
        print(json.dumps({'error': 'DeviceBox Update System - Verwendung: python3 update.py [check|update]'}, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()
