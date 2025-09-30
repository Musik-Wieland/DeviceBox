#!/usr/bin/env python3
"""
DeviceBox Fix-Update-Skript
Behebt das Berechtigungsproblem beim Update
"""

import os
import sys
import subprocess
import tempfile
import requests
import zipfile
import shutil
from datetime import datetime

def log(message):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

def run_command(cmd, check=True):
    """Führt einen Befehl aus und gibt das Ergebnis zurück"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr

def main():
    log("DeviceBox Fix-Update gestartet...")
    
    # Konfiguration
    install_dir = "/opt/devicebox"
    service_user = "pi"
    github_repo = "Musik-Wieland/DeviceBox"
    
    # Prüfe ob Installation existiert
    if not os.path.exists(install_dir):
        log("Fehler: DeviceBox ist nicht installiert!")
        return 1
    
    # Stoppe Service
    log("Stoppe DeviceBox Service...")
    success, stdout, stderr = run_command("sudo systemctl stop devicebox")
    if not success:
        log(f"Warnung beim Stoppen des Services: {stderr}")
    
    # Erstelle Backup
    backup_dir = f"/opt/devicebox-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    log(f"Erstelle Backup: {backup_dir}")
    success, stdout, stderr = run_command(f"sudo cp -r {install_dir} {backup_dir}")
    if not success:
        log(f"Fehler beim Erstellen des Backups: {stderr}")
        return 1
    
    # Setze Backup-Berechtigungen
    run_command(f"sudo chown -R {service_user}:{service_user} {backup_dir}")
    
    try:
        # Lade neueste Version von GitHub herunter
        log("Lade neueste Version von GitHub herunter...")
        url = f"https://github.com/{github_repo}/archive/main.zip"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, "repository.zip")
            
            # Download
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            
            with open(zip_path, 'wb') as f:
                f.write(response.content)
            
            # Extrahiere
            extract_dir = os.path.join(temp_dir, "extracted")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Finde das extrahierte Verzeichnis
            extracted_repo = None
            for item in os.listdir(extract_dir):
                if item.startswith("DeviceBox"):
                    extracted_repo = os.path.join(extract_dir, item)
                    break
            
            if not extracted_repo:
                raise Exception("Repository-Verzeichnis nicht gefunden")
            
            # Erstelle temporäres Verzeichnis für alte Installation
            old_install_dir = f"{install_dir}_old"
            
            # Entferne alte temporäre Installation falls vorhanden
            run_command(f"sudo rm -rf {old_install_dir}")
            
            # Verschiebe aktuelle Installation
            log(f"Verschiebe aktuelle Installation nach: {old_install_dir}")
            success, stdout, stderr = run_command(f"sudo mv {install_dir} {old_install_dir}")
            if not success:
                raise Exception(f"Fehler beim Verschieben: {stderr}")
            
            # Kopiere neue Version
            log(f"Kopiere neue Version nach: {install_dir}")
            success, stdout, stderr = run_command(f"sudo cp -r {extracted_repo} {install_dir}")
            if not success:
                raise Exception(f"Fehler beim Kopieren: {stderr}")
            
            # Stelle wichtige Dateien wieder her
            log("Stelle wichtige Dateien wieder her...")
            
            # Datenverzeichnis
            old_data_dir = os.path.join(old_install_dir, "data")
            if os.path.exists(old_data_dir):
                new_data_dir = os.path.join(install_dir, "data")
                run_command(f"sudo rm -rf {new_data_dir}")
                run_command(f"sudo cp -r {old_data_dir} {new_data_dir}")
            
            # Virtuelle Umgebung
            old_venv = os.path.join(old_install_dir, "venv")
            if os.path.exists(old_venv):
                new_venv = os.path.join(install_dir, "venv")
                run_command(f"sudo rm -rf {new_venv}")
                run_command(f"sudo cp -r {old_venv} {new_venv}")
            
            # Konfigurationsdateien
            config_files = ["config.json", "version.json"]
            for config_file in config_files:
                old_config = os.path.join(old_install_dir, config_file)
                if os.path.exists(old_config):
                    new_config = os.path.join(install_dir, config_file)
                    run_command(f"sudo cp {old_config} {new_config}")
            
            # Setze Berechtigungen
            log(f"Setze Berechtigungen für Benutzer: {service_user}")
            run_command(f"sudo chown -R {service_user}:{service_user} {install_dir}")
            
            # Setze ausführbare Berechtigungen
            executable_files = [
                "app.py", "auto_update.py", "update.py", "update_simple.py", 
                "device_manager.py", "debug_update.py", "test_update.py",
                "quick_update.sh", "update_curl.sh"
            ]
            
            for file in executable_files:
                file_path = os.path.join(install_dir, file)
                if os.path.exists(file_path):
                    run_command(f"sudo chmod +x {file_path}")
            
            # Starte Service neu
            log("Starte DeviceBox Service neu...")
            run_command("sudo systemctl daemon-reload")
            run_command("sudo systemctl start devicebox")
            
            # Prüfe Service-Status
            log("Prüfe Service-Status...")
            sleep(3)
            success, stdout, stderr = run_command("sudo systemctl is-active devicebox")
            
            if success and "active" in stdout:
                log("Service läuft erfolgreich!")
                
                # Entferne alte Installation
                log(f"Entferne alte Installation: {old_install_dir}")
                run_command(f"sudo rm -rf {old_install_dir}")
                
                # Entferne Backup
                log(f"Entferne Backup: {backup_dir}")
                run_command(f"sudo rm -rf {backup_dir}")
                
                log("Fix-Update erfolgreich abgeschlossen!")
                
                # Zeige IP-Adresse
                success, stdout, stderr = run_command("hostname -I")
                if success:
                    ip = stdout.strip().split()[0]
                    log(f"DeviceBox ist verfügbar unter: http://{ip}")
                
                return 0
            else:
                raise Exception("Service konnte nicht gestartet werden")
    
    except Exception as e:
        log(f"Fehler beim Update: {e}")
        
        # Rollback: Stelle alte Installation wieder her
        log("Führe Rollback durch...")
        try:
            if os.path.exists(old_install_dir):
                run_command(f"sudo rm -rf {install_dir}")
                run_command(f"sudo mv {old_install_dir} {install_dir}")
                run_command("sudo systemctl start devicebox")
                log("Rollback erfolgreich - alte Installation wiederhergestellt")
        except Exception as rollback_error:
            log(f"Fehler beim Rollback: {rollback_error}")
        
        return 1

if __name__ == '__main__':
    sys.exit(main())
