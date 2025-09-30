#!/usr/bin/env python3
"""
DeviceBox - Hauptanwendung für Raspberry Pi 5
Weboberfläche mit Update-Mechanismus und Gerätestatus
"""

import os
import sys
import json
import subprocess
import platform
import psutil
import requests
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from threading import Thread
import time

app = Flask(__name__)

class DeviceBoxApp:
    def __init__(self):
        self.version = "1.0.0"
        self.github_repo = os.getenv('GITHUB_REPO', 'your-username/devicebox')
        self.app_name = os.getenv('APP_NAME', 'devicebox')
        self.update_in_progress = False
        
    def get_system_info(self):
        """Sammelt Systeminformationen"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Raspberry Pi spezifische Informationen
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    cpuinfo = f.read()
                    model = [line for line in cpuinfo.split('\n') if 'Model' in line][0].split(':')[1].strip()
            except:
                model = "Raspberry Pi"
            
            return {
                'hostname': platform.node(),
                'platform': platform.platform(),
                'cpu_model': model,
                'cpu_percent': cpu_percent,
                'memory_total': memory.total,
                'memory_used': memory.used,
                'memory_percent': memory.percent,
                'disk_total': disk.total,
                'disk_used': disk.used,
                'disk_percent': (disk.used / disk.total) * 100,
                'uptime': self.get_uptime(),
                'temperature': self.get_cpu_temperature(),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_uptime(self):
        """Gibt die Uptime des Systems zurück"""
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.read().split()[0])
                return uptime_seconds
        except:
            return 0
    
    def get_cpu_temperature(self):
        """Gibt die CPU-Temperatur zurück (Raspberry Pi)"""
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = int(f.read()) / 1000.0
                return temp
        except:
            return None
    
    def check_for_updates(self):
        """Prüft auf verfügbare Updates auf GitHub"""
        try:
            url = f"https://api.github.com/repos/{self.github_repo}/releases/latest"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                latest_release = response.json()
                latest_version = latest_release['tag_name'].lstrip('v')
                
                return {
                    'available': latest_version != self.version,
                    'latest_version': latest_version,
                    'current_version': self.version,
                    'release_notes': latest_release.get('body', ''),
                    'download_url': latest_release['assets'][0]['browser_download_url'] if latest_release['assets'] else None
                }
            else:
                return {'error': f'GitHub API Fehler: {response.status_code}'}
        except Exception as e:
            return {'error': str(e)}
    
    def perform_update(self):
        """Führt das Update durch"""
        if self.update_in_progress:
            return {'error': 'Update bereits in Bearbeitung'}
        
        self.update_in_progress = True
        
        try:
            # Update-Skript ausführen
            update_script = os.path.join(os.path.dirname(__file__), 'update.py')
            if os.path.exists(update_script):
                result = subprocess.run([sys.executable, update_script], 
                                      capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    return {'success': True, 'message': 'Update erfolgreich abgeschlossen'}
                else:
                    return {'error': f'Update fehlgeschlagen: {result.stderr}'}
            else:
                return {'error': 'Update-Skript nicht gefunden'}
        except Exception as e:
            return {'error': str(e)}
        finally:
            self.update_in_progress = False

# Globale App-Instanz
devicebox = DeviceBoxApp()

@app.route('/')
def index():
    """Hauptseite"""
    return render_template('index.html', version=devicebox.version)

@app.route('/api/status')
def api_status():
    """API-Endpoint für Gerätestatus"""
    return jsonify(devicebox.get_system_info())

@app.route('/api/check-updates')
def api_check_updates():
    """API-Endpoint für Update-Check"""
    return jsonify(devicebox.check_for_updates())

@app.route('/api/update', methods=['POST'])
def api_update():
    """API-Endpoint für Update-Durchführung"""
    return jsonify(devicebox.perform_update())

@app.route('/api/version')
def api_version():
    """API-Endpoint für Version"""
    return jsonify({'version': devicebox.version})

if __name__ == '__main__':
    # Konfiguration aus Umgebungsvariablen
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8080))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    print(f"DeviceBox v{devicebox.version} startet auf {host}:{port}")
    app.run(host=host, port=port, debug=debug)
