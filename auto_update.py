#!/usr/bin/env python3
"""
DeviceBox Auto-Update System
Lädt Updates direkt von GitHub ohne Release-Erstellung
"""

import os
import sys
import json
import shutil
import requests
import subprocess
import tempfile
import hashlib
from pathlib import Path
from datetime import datetime

class DeviceBoxAutoUpdater:
    def __init__(self):
        self.github_repo = os.getenv('GITHUB_REPO', 'Musik-Wieland/DeviceBox')
        self.app_name = os.getenv('APP_NAME', 'devicebox')
        self.install_dir = os.getenv('INSTALL_DIR', '/opt/devicebox')
        self.data_dir = os.getenv('DATA_DIR', '/opt/devicebox/data')
        self.config_file = os.path.join(self.install_dir, 'config.json')
        self.version_file = os.path.join(self.install_dir, 'version.json')
        
    def get_current_version(self):
        """Gibt die aktuelle Version zurück"""
        try:
            if os.path.exists(self.version_file):
                with open(self.version_file, 'r') as f:
                    data = json.load(f)
                    return data.get('version', '1.0.0')
            return '1.0.0'
        except Exception:
            return '1.0.0'
    
    def get_latest_commit_hash(self):
        """Holt den neuesten Commit-Hash von GitHub"""
        try:
            url = f"https://api.github.com/repos/{self.github_repo}/commits/main"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                commit_data = response.json()
                return commit_data['sha'], commit_data['commit']['message']
            else:
                raise Exception(f"GitHub API Fehler: {response.status_code}")
        except Exception as e:
            raise Exception(f"Fehler beim Abrufen der Commit-Informationen: {e}")
    
    def download_repository(self, temp_dir):
        """Lädt das komplette Repository herunter"""
        try:
            print(f"Lade Repository von GitHub herunter...")
            
            # Erstelle ZIP-URL für den main branch
            zip_url = f"https://github.com/{self.github_repo}/archive/refs/heads/main.zip"
            
            response = requests.get(zip_url, timeout=300, stream=True)
            response.raise_for_status()
            
            zip_path = os.path.join(temp_dir, 'repository.zip')
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"Repository heruntergeladen: {zip_path}")
            return zip_path
        except Exception as e:
            raise Exception(f"Fehler beim Herunterladen: {e}")
    
    def extract_repository(self, zip_path, temp_dir):
        """Extrahiert das Repository-Archiv"""
        try:
            import zipfile
            
            extract_dir = os.path.join(temp_dir, 'extracted')
            os.makedirs(extract_dir, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Finde den extrahierten Ordner (hat den Namen des Repositories)
            extracted_folders = [f for f in os.listdir(extract_dir) if os.path.isdir(os.path.join(extract_dir, f))]
            if not extracted_folders:
                raise Exception("Kein extrahierter Ordner gefunden")
            
            repo_folder = os.path.join(extract_dir, extracted_folders[0])
            print(f"Repository extrahiert nach: {repo_folder}")
            return repo_folder
        except Exception as e:
            raise Exception(f"Fehler beim Extrahieren: {e}")
    
    def backup_data(self):
        """Erstellt ein Backup der wichtigen Daten"""
        try:
            backup_dir = os.path.join(self.install_dir, 'backup')
            os.makedirs(backup_dir, exist_ok=True)
            
            # Backup-Zeitstempel
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(backup_dir, f'backup_{timestamp}')
            os.makedirs(backup_path, exist_ok=True)
            
            # Wichtige Dateien und Verzeichnisse sichern
            items_to_backup = [
                self.data_dir,
                self.config_file,
                self.version_file,
                '/etc/systemd/system/devicebox.service'  # Systemd-Service
            ]
            
            for item in items_to_backup:
                if os.path.exists(item):
                    if os.path.isdir(item):
                        shutil.copytree(item, os.path.join(backup_path, os.path.basename(item)))
                    else:
                        shutil.copy2(item, backup_path)
            
            print(f"Backup erstellt: {backup_path}")
            return backup_path
        except Exception as e:
            raise Exception(f"Fehler beim Erstellen des Backups: {e}")
    
    def install_update(self, extracted_dir):
        """Installiert das Update"""
        try:
            # Stoppe den Service
            print("Stoppe DeviceBox Service...")
            subprocess.run(['sudo', 'systemctl', 'stop', 'devicebox'], check=True)
            
            # Erstelle temporäres Verzeichnis für alte Installation
            old_install_dir = f"{self.install_dir}_old"
            if os.path.exists(old_install_dir):
                subprocess.run(['sudo', 'rm', '-rf', old_install_dir], check=True)
            
            # Verschiebe aktuelle Installation mit sudo
            if os.path.exists(self.install_dir):
                print(f"Verschiebe aktuelle Installation nach: {old_install_dir}")
                subprocess.run(['sudo', 'mv', self.install_dir, old_install_dir], check=True)
            
            # Kopiere neue Version mit sudo
            print(f"Kopiere neue Version nach: {self.install_dir}")
            subprocess.run(['sudo', 'cp', '-r', extracted_dir, self.install_dir], check=True)
            
            # Stelle wichtige Dateien wieder her
            self.restore_data(old_install_dir)
            
            # Setze Berechtigungen
            service_user = os.getenv('SERVICE_USER', 'pi')
            print(f"Setze Berechtigungen für Benutzer: {service_user}")
            subprocess.run(['sudo', 'chown', '-R', f'{service_user}:{service_user}', self.install_dir], check=True)
            
            # Setze ausführbare Berechtigungen für alle Python-Skripte
            executable_files = ['app.py', 'auto_update.py', 'update.py', 'update_simple.py', 'device_manager.py', 'debug_update.py', 'test_update.py']
            for file in executable_files:
                file_path = os.path.join(self.install_dir, file)
                if os.path.exists(file_path):
                    subprocess.run(['sudo', 'chmod', '+x', file_path], check=True)
            
            # Aktualisiere Version
            self.update_version_file()
            
            # Starte Service neu
            print("Starte DeviceBox Service neu...")
            subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=True)
            subprocess.run(['sudo', 'systemctl', 'start', 'devicebox'], check=True)
            
            # Prüfe Service-Status
            sleep(3)
            result = subprocess.run(['sudo', 'systemctl', 'is-active', 'devicebox'], capture_output=True, text=True)
            if result.returncode == 0 and 'active' in result.stdout:
                print("Service läuft erfolgreich")
                
                # Entferne alte Installation nach erfolgreichem Start
                print(f"Entferne alte Installation: {old_install_dir}")
                subprocess.run(['sudo', 'rm', '-rf', old_install_dir], check=True)
                
                print("Update erfolgreich installiert!")
                return True
            else:
                raise Exception("Service konnte nicht gestartet werden")
                
        except Exception as e:
            print(f"Fehler bei der Installation: {e}")
            
            # Bei Fehler: Stelle alte Installation wieder her
            try:
                if os.path.exists(old_install_dir):
                    print("Stelle alte Installation wieder her...")
                    if os.path.exists(self.install_dir):
                        subprocess.run(['sudo', 'rm', '-rf', self.install_dir], check=True)
                    subprocess.run(['sudo', 'mv', old_install_dir, self.install_dir], check=True)
                    subprocess.run(['sudo', 'systemctl', 'start', 'devicebox'], check=False)
                    print("Alte Installation wiederhergestellt")
            except Exception as restore_error:
                print(f"Fehler beim Wiederherstellen: {restore_error}")
            
            raise Exception(f"Fehler bei der Installation: {e}")
    
    def restore_data(self, old_install_dir):
        """Stellt wichtige Daten aus der alten Installation wieder her"""
        try:
            # Stelle Datenverzeichnis wieder her
            old_data_dir = os.path.join(old_install_dir, 'data')
            if os.path.exists(old_data_dir):
                if os.path.exists(self.data_dir):
                    subprocess.run(['sudo', 'rm', '-rf', self.data_dir], check=True)
                subprocess.run(['sudo', 'cp', '-r', old_data_dir, self.data_dir], check=True)
            
            # Stelle Konfigurationsdatei wieder her
            old_config = os.path.join(old_install_dir, 'config.json')
            if os.path.exists(old_config):
                subprocess.run(['sudo', 'cp', old_config, self.config_file], check=True)
            
            # Stelle virtuelle Umgebung wieder her falls vorhanden
            old_venv = os.path.join(old_install_dir, 'venv')
            if os.path.exists(old_venv):
                new_venv = os.path.join(self.install_dir, 'venv')
                if os.path.exists(new_venv):
                    subprocess.run(['sudo', 'rm', '-rf', new_venv], check=True)
                subprocess.run(['sudo', 'cp', '-r', old_venv, new_venv], check=True)
            
            print("Daten erfolgreich wiederhergestellt")
        except Exception as e:
            print(f"Warnung beim Wiederherstellen der Daten: {e}")
    
    def update_version_file(self):
        """Aktualisiert die Versionsdatei"""
        try:
            commit_hash, commit_message = self.get_latest_commit_hash()
            version_data = {
                'version': f"1.0.{commit_hash[:8]}",
                'commit_hash': commit_hash,
                'commit_message': commit_message,
                'updated_at': datetime.now().isoformat()
            }
            
            with open(self.version_file, 'w') as f:
                json.dump(version_data, f, indent=2)
            
            print(f"Version aktualisiert: {version_data['version']}")
        except Exception as e:
            print(f"Warnung beim Aktualisieren der Version: {e}")
    
    def check_for_updates(self):
        """Prüft auf verfügbare Updates"""
        try:
            current_version = self.get_current_version()
            commit_hash, commit_message = self.get_latest_commit_hash()
            
            # Vergleiche mit gespeichertem Commit-Hash
            stored_hash = ''
            if os.path.exists(self.version_file):
                try:
                    with open(self.version_file, 'r') as f:
                        version_data = json.load(f)
                        stored_hash = version_data.get('commit_hash', '')
                except Exception as e:
                    print(f"Fehler beim Lesen der Version-Datei: {e}")
                    stored_hash = ''
            
            # Wenn keine gespeicherte Version vorhanden ist, aktualisiere die Version-Datei
            if not stored_hash:
                self.update_version_file()
                return {
                    'available': False,
                    'current_version': current_version,
                    'latest_version': f"1.0.{commit_hash[:8]}",
                    'message': 'Version-Datei aktualisiert'
                }
            
            if commit_hash == stored_hash:
                return {
                    'available': False,
                    'current_version': current_version,
                    'latest_version': f"1.0.{commit_hash[:8]}",
                    'message': 'System ist aktuell'
                }
            
            return {
                'available': True,
                'current_version': current_version,
                'latest_version': f"1.0.{commit_hash[:8]}",
                'commit_message': commit_message,
                'message': 'Update verfügbar'
            }
        except Exception as e:
            return {'error': str(e)}
    
    def update(self):
        """Führt das komplette Update durch"""
        try:
            print("DeviceBox Auto-Update gestartet...")
            
            # Prüfe auf Updates
            update_info = self.check_for_updates()
            if not update_info.get('available', False):
                print(f"Kein Update verfügbar: {update_info.get('message', 'System ist aktuell')}")
                return True
            
            print(f"Update verfügbar: {update_info['latest_version']}")
            
            # Erstelle temporäres Verzeichnis
            with tempfile.TemporaryDirectory() as temp_dir:
                # Backup erstellen
                self.backup_data()
                
                # Repository herunterladen
                zip_path = self.download_repository(temp_dir)
                
                # Repository extrahieren
                extracted_dir = self.extract_repository(zip_path, temp_dir)
                
                # Update installieren
                self.install_update(extracted_dir)
            
            print("Auto-Update erfolgreich abgeschlossen!")
            return True
            
        except Exception as e:
            print(f"Auto-Update fehlgeschlagen: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Hauptfunktion für Auto-Update-Skript"""
    updater = DeviceBoxAutoUpdater()
    
    if len(sys.argv) > 1 and sys.argv[1] == 'check':
        # Nur auf Updates prüfen
        update_info = updater.check_for_updates()
        print(json.dumps(update_info, indent=2))
    else:
        # Vollständiges Update durchführen
        try:
            success = updater.update()
            if success:
                print("Update erfolgreich abgeschlossen")
            else:
                print("Update fehlgeschlagen")
            sys.exit(0 if success else 1)
        except Exception as e:
            print(f"Kritischer Fehler beim Update: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == '__main__':
    main()
