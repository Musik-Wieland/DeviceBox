#!/usr/bin/env python3
"""
Update Manager für DeviceBox
Verwaltet Updates über GitHub Repository
"""

import os
import json
import requests
import subprocess
import shutil
from datetime import datetime
from git import Repo

class UpdateManager:
    def __init__(self):
        self.repo_url = "https://github.com/yourusername/devicebox.git"
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.version_file = os.path.join(self.current_dir, 'version.json')
        self.backup_dir = os.path.join(self.current_dir, 'backup')
        
    def get_current_version(self):
        """Aktuelle Version abrufen"""
        try:
            if os.path.exists(self.version_file):
                with open(self.version_file, 'r') as f:
                    version_data = json.load(f)
                return {
                    'version': version_data.get('version', '1.0.0'),
                    'build_date': version_data.get('build_date', 'Unknown'),
                    'commit_hash': version_data.get('commit_hash', 'Unknown')
                }
            else:
                return {
                    'version': '1.0.0',
                    'build_date': 'Unknown',
                    'commit_hash': 'Unknown'
                }
        except Exception as e:
            return {'error': str(e)}
    
    def check_for_updates(self):
        """Auf Updates prüfen"""
        try:
            # GitHub API für neueste Release
            api_url = "https://api.github.com/repos/yourusername/devicebox/releases/latest"
            
            # Für private Repositories: GitHub Token verwenden
            headers = {}
            github_token = os.getenv('GITHUB_TOKEN')
            if github_token:
                headers['Authorization'] = f'token {github_token}'
            
            response = requests.get(api_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                release_data = response.json()
                latest_version = release_data['tag_name'].replace('v', '')
                current_version = self.get_current_version()['version']
                
                return {
                    'current_version': current_version,
                    'latest_version': latest_version,
                    'update_available': self._compare_versions(current_version, latest_version),
                    'release_notes': release_data.get('body', ''),
                    'download_url': release_data['zipball_url']
                }
            else:
                return {'error': 'GitHub API nicht erreichbar'}
                
        except Exception as e:
            return {'error': str(e)}
    
    def _compare_versions(self, current, latest):
        """Versionen vergleichen"""
        try:
            current_parts = [int(x) for x in current.split('.')]
            latest_parts = [int(x) for x in latest.split('.')]
            
            for i in range(max(len(current_parts), len(latest_parts))):
                current_part = current_parts[i] if i < len(current_parts) else 0
                latest_part = latest_parts[i] if i < len(latest_parts) else 0
                
                if latest_part > current_part:
                    return True
                elif latest_part < current_part:
                    return False
            
            return False
        except:
            return False
    
    def perform_update(self):
        """Update durchführen"""
        try:
            # Backup erstellen
            self._create_backup()
            
            # Update durchführen
            update_info = self.check_for_updates()
            if not update_info.get('update_available'):
                return {'status': 'no_update', 'message': 'Kein Update verfügbar'}
            
            # Temporäres Verzeichnis für Update
            temp_dir = '/tmp/devicebox_update'
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            
            # Repository klonen (mit Token für private Repos)
            github_token = os.getenv('GITHUB_TOKEN')
            if github_token:
                # Private Repository mit Token
                repo_url_with_token = self.repo_url.replace('https://', f'https://{github_token}@')
                repo = Repo.clone_from(repo_url_with_token, temp_dir)
            else:
                # Öffentliches Repository
                repo = Repo.clone_from(self.repo_url, temp_dir)
            
            # Dateien kopieren (außer Konfigurationsdateien)
            exclude_files = ['config.json', 'data/', 'logs/', 'backup/']
            
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    src_path = os.path.join(root, file)
                    rel_path = os.path.relpath(src_path, temp_dir)
                    
                    # Konfigurationsdateien überspringen
                    if any(exclude in rel_path for exclude in exclude_files):
                        continue
                    
                    dst_path = os.path.join(self.current_dir, rel_path)
                    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                    shutil.copy2(src_path, dst_path)
            
            # Version aktualisieren
            self._update_version_file(update_info['latest_version'])
            
            # Temporäres Verzeichnis löschen
            shutil.rmtree(temp_dir)
            
            return {
                'status': 'success',
                'message': f'Update auf Version {update_info["latest_version"]} erfolgreich',
                'new_version': update_info['latest_version']
            }
            
        except Exception as e:
            # Bei Fehler Backup wiederherstellen
            self._restore_backup()
            return {'status': 'error', 'message': str(e)}
    
    def _create_backup(self):
        """Backup erstellen"""
        try:
            if os.path.exists(self.backup_dir):
                shutil.rmtree(self.backup_dir)
            
            shutil.copytree(self.current_dir, self.backup_dir, 
                          ignore=shutil.ignore_patterns('backup', '__pycache__', '*.pyc'))
        except Exception as e:
            print(f"Backup-Fehler: {e}")
    
    def _restore_backup(self):
        """Backup wiederherstellen"""
        try:
            if os.path.exists(self.backup_dir):
                for root, dirs, files in os.walk(self.backup_dir):
                    for file in files:
                        src_path = os.path.join(root, file)
                        rel_path = os.path.relpath(src_path, self.backup_dir)
                        dst_path = os.path.join(self.current_dir, rel_path)
                        
                        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                        shutil.copy2(src_path, dst_path)
        except Exception as e:
            print(f"Backup-Wiederherstellung Fehler: {e}")
    
    def _update_version_file(self, new_version):
        """Version-Datei aktualisieren"""
        try:
            version_data = {
                'version': new_version,
                'build_date': datetime.now().isoformat(),
                'commit_hash': 'Unknown'
            }
            
            with open(self.version_file, 'w') as f:
                json.dump(version_data, f, indent=2)
        except Exception as e:
            print(f"Version-Datei Update Fehler: {e}")
