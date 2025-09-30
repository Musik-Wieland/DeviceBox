#!/usr/bin/env python3
"""
DeviceBox Update System
Professionelles Update-System mit bewährten Bibliotheken
"""

import os
import sys
import json
import shutil
import subprocess
import tempfile
import zipfile
import requests
from packaging import version
from pathlib import Path
import logging

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DeviceBoxUpdater:
    """Professionelles Update-System für DeviceBox"""
    
    def __init__(self):
        self.repo_owner = "Musik-Wieland"
        self.repo_name = "DeviceBox"
        self.github_api_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}"
        self.install_dir = Path("/opt/devicebox")
        self.version_file = self.install_dir / "version.json"
        self.current_version = self.get_current_version()
        
    def get_current_version(self):
        """Aktuelle Version aus version.json lesen"""
        try:
            if self.version_file.exists():
                with open(self.version_file, 'r') as f:
                    data = json.load(f)
                    return data.get('version', '1.0.0')
            return '1.0.0'
        except Exception as e:
            logger.warning(f"Fehler beim Lesen der Version: {e}")
            return '1.0.0'
    
    def get_latest_release(self):
        """Neueste Release von GitHub API abrufen"""
        try:
            url = f"{self.github_api_url}/releases/latest"
            headers = {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'DeviceBox-Updater'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            release_data = response.json()
            return {
                'version': release_data['tag_name'].lstrip('v'),
                'download_url': release_data['zipball_url'],
                'published_at': release_data['published_at'],
                'body': release_data.get('body', '')
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"GitHub API Fehler: {e}")
            return None
        except Exception as e:
            logger.error(f"Unerwarteter Fehler: {e}")
            return None
    
    def is_update_available(self):
        """Prüft ob ein Update verfügbar ist"""
        latest_release = self.get_latest_release()
        if not latest_release:
            return False
            
        current_ver = version.parse(self.current_version)
        latest_ver = version.parse(latest_release['version'])
        
        return latest_ver > current_ver
    
    def check_for_updates(self):
        """Prüft auf Updates und gibt JSON zurück"""
        try:
            latest_release = self.get_latest_release()
            if not latest_release:
                return {'error': 'Keine Release-Informationen verfügbar'}
            
            current_ver = version.parse(self.current_version)
            latest_ver = version.parse(latest_release['version'])
            
            update_available = latest_ver > current_ver
            
            result = {
                'current_version': self.current_version,
                'latest_version': latest_release['version'],
                'update_available': update_available,
                'published_at': latest_release['published_at'],
                'release_notes': latest_release['body']
            }
            
            if update_available:
                result['update_info'] = f"Update verfügbar: {self.current_version} → {latest_release['version']}"
            
            return result
            
        except Exception as e:
            logger.error(f"Fehler beim Update-Check: {e}")
            return {'error': str(e)}
    
    def download_release(self, release_info):
        """Release herunterladen"""
        try:
            logger.info(f"Lade Release {release_info['version']} herunter...")
            
            response = requests.get(release_info['download_url'], timeout=60)
            response.raise_for_status()
            
            # Temporäre Datei erstellen
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
            temp_file.write(response.content)
            temp_file.close()
            
            logger.info(f"Release heruntergeladen: {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Fehler beim Herunterladen: {e}")
            raise
    
    def extract_release(self, zip_path):
        """Release extrahieren"""
        try:
            extract_dir = tempfile.mkdtemp()
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # GitHub erstellt ein Unterverzeichnis, finde es
            extracted_items = os.listdir(extract_dir)
            if len(extracted_items) == 1:
                actual_extract_dir = os.path.join(extract_dir, extracted_items[0])
            else:
                actual_extract_dir = extract_dir
            
            logger.info(f"Release extrahiert nach: {actual_extract_dir}")
            return actual_extract_dir
            
        except Exception as e:
            logger.error(f"Fehler beim Extrahieren: {e}")
            raise
    
    def create_backup(self):
        """Backup der aktuellen Installation erstellen"""
        try:
            backup_dir = f"{self.install_dir}_backup_{self.current_version.replace('.', '_')}"
            
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            
            shutil.copytree(self.install_dir, backup_dir)
            logger.info(f"Backup erstellt: {backup_dir}")
            return backup_dir
            
        except Exception as e:
            logger.error(f"Fehler beim Backup: {e}")
            raise
    
    def install_update(self, extracted_dir):
        """Update installieren"""
        try:
            logger.info("Installiere Update...")
            
            # Service stoppen (nur auf Raspberry Pi)
            if self.is_raspberry_pi():
                logger.info("Stoppe DeviceBox Service...")
                self.run_sudo_command(['systemctl', 'stop', 'devicebox'])
            
            # Backup erstellen
            backup_dir = self.create_backup()
            
            # Alte Installation temporär verschieben
            old_dir = f"{self.install_dir}_old"
            if old_dir.exists():
                shutil.rmtree(old_dir)
            
            if self.install_dir.exists():
                shutil.move(str(self.install_dir), old_dir)
            
            # Neue Installation kopieren
            logger.info(f"Kopiere neue Version nach: {self.install_dir}")
            shutil.copytree(extracted_dir, str(self.install_dir))
            
            # Wichtige Daten wiederherstellen
            self.restore_user_data(old_dir)
            
            # Berechtigungen setzen (nur auf Raspberry Pi)
            if self.is_raspberry_pi():
                self.set_permissions()
            
            # Version aktualisieren
            self.update_version_file()
            
            # Service neu starten (nur auf Raspberry Pi)
            if self.is_raspberry_pi():
                logger.info("Starte DeviceBox Service neu...")
                self.run_sudo_command(['systemctl', 'daemon-reload'])
                self.run_sudo_command(['systemctl', 'start', 'devicebox'])
                
                # Service-Status prüfen
                import time
                time.sleep(3)
                result = self.run_sudo_command(['systemctl', 'is-active', 'devicebox'], capture_output=True)
                if result.returncode != 0 or 'active' not in result.stdout:
                    raise Exception("Service konnte nicht gestartet werden")
            
            # Alte Installation entfernen
            if old_dir.exists():
                shutil.rmtree(old_dir)
            
            logger.info("Update erfolgreich installiert!")
            return True
            
        except Exception as e:
            logger.error(f"Fehler bei der Installation: {e}")
            # Rollback bei Fehler
            self.rollback_update(old_dir, backup_dir)
            raise
    
    def restore_user_data(self, old_dir):
        """Wichtige Benutzerdaten wiederherstellen"""
        try:
            old_path = Path(old_dir)
            
            # Wichtige Verzeichnisse und Dateien
            important_items = [
                'data',
                'config.json',
                'devices.json',
                'logs',
                'venv'
            ]
            
            for item in important_items:
                old_item = old_path / item
                new_item = self.install_dir / item
                
                if old_item.exists():
                    if old_item.is_dir():
                        if new_item.exists():
                            shutil.rmtree(new_item)
                        shutil.copytree(str(old_item), str(new_item))
                    else:
                        shutil.copy2(str(old_item), str(new_item))
                    
                    logger.info(f"Wiederhergestellt: {item}")
            
        except Exception as e:
            logger.warning(f"Fehler beim Wiederherstellen der Daten: {e}")
    
    def set_permissions(self):
        """Berechtigungen für Raspberry Pi setzen"""
        try:
            service_user = os.getenv('SERVICE_USER', 'pi')
            logger.info(f"Setze Berechtigungen für Benutzer: {service_user}")
            
            self.run_sudo_command(['chown', '-R', f'{service_user}:{service_user}', 
                          str(self.install_dir)])
            
            # Ausführbare Berechtigungen
            executable_files = ['app.py', 'update_system.py', 'device_manager.py']
            for file in executable_files:
                file_path = self.install_dir / file
                if file_path.exists():
                    self.run_sudo_command(['chmod', '+x', str(file_path)])
            
        except Exception as e:
            logger.warning(f"Fehler beim Setzen der Berechtigungen: {e}")
    
    def update_version_file(self):
        """Version-Datei aktualisieren"""
        try:
            latest_release = self.get_latest_release()
            version_data = {
                'version': latest_release['version'],
                'updated_at': latest_release['published_at']
            }
            
            with open(self.version_file, 'w') as f:
                json.dump(version_data, f, indent=2)
            
            logger.info(f"Version aktualisiert: {latest_release['version']}")
            
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren der Version: {e}")
    
    def rollback_update(self, old_dir, backup_dir):
        """Rollback bei Fehler"""
        try:
            logger.info("Führe Rollback durch...")
            
            if old_dir.exists():
                if self.install_dir.exists():
                    shutil.rmtree(self.install_dir)
                shutil.move(old_dir, str(self.install_dir))
            
            if self.is_raspberry_pi():
                self.run_sudo_command(['systemctl', 'start', 'devicebox'], check=False)
            
            logger.info("Rollback erfolgreich")
            
        except Exception as e:
            logger.error(f"Fehler beim Rollback: {e}")
    
    def is_raspberry_pi(self):
        """Prüft ob wir auf einem Raspberry Pi sind"""
        return os.path.exists('/etc/os-release') and 'raspbian' in open('/etc/os-release').read().lower()
    
    def run_sudo_command(self, command, check=True, capture_output=False):
        """Führt einen Befehl mit sudo aus, falls verfügbar"""
        try:
            # Prüfe ob sudo verfügbar ist
            if shutil.which('sudo'):
                cmd = ['sudo'] + command
            else:
                # Fallback: Versuche ohne sudo (falls bereits als root)
                cmd = command
                logger.warning("sudo nicht verfügbar, führe Befehl ohne sudo aus")
            
            return subprocess.run(cmd, check=check, capture_output=capture_output, text=True)
            
        except FileNotFoundError:
            # Falls sudo nicht gefunden wird, versuche ohne sudo
            logger.warning("sudo nicht gefunden, führe Befehl ohne sudo aus")
            return subprocess.run(command, check=check, capture_output=capture_output, text=True)
        except Exception as e:
            logger.error(f"Fehler beim Ausführen des Befehls: {e}")
            raise
    
    def perform_update(self):
        """Komplettes Update durchführen"""
        try:
            logger.info("DeviceBox Update gestartet...")
            
            # Update verfügbar?
            if not self.is_update_available():
                logger.info("Kein Update verfügbar")
                return False
            
            latest_release = self.get_latest_release()
            logger.info(f"Update verfügbar: {self.current_version} → {latest_release['version']}")
            
            # Release herunterladen
            zip_path = self.download_release(latest_release)
            
            try:
                # Release extrahieren
                extracted_dir = self.extract_release(zip_path)
                
                try:
                    # Update installieren
                    self.install_update(extracted_dir)
                    logger.info("Update erfolgreich abgeschlossen!")
                    return True
                    
                finally:
                    # Temporäre Verzeichnisse aufräumen
                    if os.path.exists(extracted_dir):
                        shutil.rmtree(extracted_dir)
                        
            finally:
                # ZIP-Datei löschen
                if os.path.exists(zip_path):
                    os.unlink(zip_path)
            
        except Exception as e:
            logger.error(f"Update fehlgeschlagen: {e}")
            return False

def main():
    """Hauptfunktion"""
    if len(sys.argv) < 2:
        print("Verwendung: python3 update_system.py [check|update]")
        sys.exit(1)
    
    command = sys.argv[1]
    updater = DeviceBoxUpdater()
    
    if command == 'check':
        result = updater.check_for_updates()
        print(json.dumps(result, indent=2))
        
    elif command == 'update':
        success = updater.perform_update()
        sys.exit(0 if success else 1)
        
    else:
        print("Unbekannter Befehl. Verwende 'check' oder 'update'")
        sys.exit(1)

if __name__ == '__main__':
    main()
