#!/usr/bin/env python3
"""
DeviceBox Update-System
Führt Updates ohne Datenverlust durch
"""

import os
import sys
import json
import shutil
import requests
import subprocess
import tempfile
from pathlib import Path

class DeviceBoxUpdater:
    def __init__(self):
        self.github_repo = os.getenv('GITHUB_REPO', 'your-username/devicebox')
        self.app_name = os.getenv('APP_NAME', 'devicebox')
        self.install_dir = os.getenv('INSTALL_DIR', '/opt/devicebox')
        self.data_dir = os.getenv('DATA_DIR', '/opt/devicebox/data')
        self.config_file = os.path.join(self.install_dir, 'config.json')
        
    def get_latest_release(self):
        """Holt die neueste Release-Information von GitHub"""
        try:
            url = f"https://api.github.com/repos/{self.github_repo}/releases/latest"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"GitHub API Fehler: {response.status_code}")
        except Exception as e:
            raise Exception(f"Fehler beim Abrufen der Release-Informationen: {e}")
    
    def download_release(self, download_url, temp_dir):
        """Lädt die neueste Version herunter"""
        try:
            print(f"Lade Update von {download_url} herunter...")
            response = requests.get(download_url, timeout=300, stream=True)
            response.raise_for_status()
            
            # Bestimme Dateiname aus URL oder Content-Disposition
            filename = download_url.split('/')[-1]
            if not filename.endswith('.zip'):
                filename = f"{self.app_name}-update.zip"
            
            filepath = os.path.join(temp_dir, filename)
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"Update heruntergeladen: {filepath}")
            return filepath
        except Exception as e:
            raise Exception(f"Fehler beim Herunterladen: {e}")
    
    def backup_data(self):
        """Erstellt ein Backup der wichtigen Daten"""
        try:
            backup_dir = os.path.join(self.install_dir, 'backup')
            os.makedirs(backup_dir, exist_ok=True)
            
            # Backup-Zeitstempel
            timestamp = subprocess.check_output(['date', '+%Y%m%d_%H%M%S']).decode().strip()
            backup_path = os.path.join(backup_dir, f'backup_{timestamp}')
            
            # Wichtige Dateien und Verzeichnisse sichern
            items_to_backup = [
                self.data_dir,
                self.config_file,
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
    
    def extract_update(self, zip_path, temp_dir):
        """Extrahiert das Update-Archiv"""
        try:
            import zipfile
            
            extract_dir = os.path.join(temp_dir, 'extracted')
            os.makedirs(extract_dir, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            print(f"Update extrahiert nach: {extract_dir}")
            return extract_dir
        except Exception as e:
            raise Exception(f"Fehler beim Extrahieren: {e}")
    
    def install_update(self, extracted_dir):
        """Installiert das Update"""
        try:
            # Stoppe den Service
            print("Stoppe DeviceBox Service...")
            subprocess.run(['sudo', 'systemctl', 'stop', 'devicebox'], check=True)
            
            # Erstelle temporäres Verzeichnis für alte Installation
            old_install_dir = f"{self.install_dir}_old"
            if os.path.exists(old_install_dir):
                shutil.rmtree(old_install_dir)
            
            # Verschiebe aktuelle Installation
            if os.path.exists(self.install_dir):
                shutil.move(self.install_dir, old_install_dir)
            
            # Kopiere neue Version
            shutil.copytree(extracted_dir, self.install_dir)
            
            # Stelle wichtige Dateien wieder her
            self.restore_data(old_install_dir)
            
            # Setze Berechtigungen
            subprocess.run(['sudo', 'chown', '-R', 'pi:pi', self.install_dir], check=True)
            subprocess.run(['sudo', 'chmod', '+x', os.path.join(self.install_dir, 'app.py')], check=True)
            
            # Starte Service neu
            print("Starte DeviceBox Service neu...")
            subprocess.run(['sudo', 'systemctl', 'start', 'devicebox'], check=True)
            
            # Entferne alte Installation nach erfolgreichem Start
            shutil.rmtree(old_install_dir)
            
            print("Update erfolgreich installiert!")
            return True
        except Exception as e:
            # Bei Fehler: Stelle alte Installation wieder her
            if os.path.exists(old_install_dir):
                if os.path.exists(self.install_dir):
                    shutil.rmtree(self.install_dir)
                shutil.move(old_install_dir, self.install_dir)
                subprocess.run(['sudo', 'systemctl', 'start', 'devicebox'], check=False)
            
            raise Exception(f"Fehler bei der Installation: {e}")
    
    def restore_data(self, old_install_dir):
        """Stellt wichtige Daten aus der alten Installation wieder her"""
        try:
            # Stelle Datenverzeichnis wieder her
            old_data_dir = os.path.join(old_install_dir, 'data')
            if os.path.exists(old_data_dir):
                if os.path.exists(self.data_dir):
                    shutil.rmtree(self.data_dir)
                shutil.copytree(old_data_dir, self.data_dir)
            
            # Stelle Konfigurationsdatei wieder her
            old_config = os.path.join(old_install_dir, 'config.json')
            if os.path.exists(old_config):
                shutil.copy2(old_config, self.config_file)
            
            print("Daten erfolgreich wiederhergestellt")
        except Exception as e:
            print(f"Warnung beim Wiederherstellen der Daten: {e}")
    
    def update(self):
        """Führt das komplette Update durch"""
        try:
            print("DeviceBox Update gestartet...")
            
            # Hole Release-Informationen
            release_info = self.get_latest_release()
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
    """Hauptfunktion für Update-Skript"""
    updater = DeviceBoxUpdater()
    success = updater.update()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
