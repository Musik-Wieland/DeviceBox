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
from device_manager import device_manager

app = Flask(__name__)

class DeviceBoxApp:
    def __init__(self):
        self.version = "1.0.0"
        self.github_repo = os.getenv('GITHUB_REPO', 'Musik-Wieland/DeviceBox')
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
        """Prüft auf verfügbare Updates mit professionellem Update-System"""
        try:
            # Verwende das neue professionelle Update-System
            import subprocess
            result = subprocess.run([
                sys.executable, 
                os.path.join(os.path.dirname(__file__), 'update_system.py'), 
                'check'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                try:
                    import json
                    update_info = json.loads(result.stdout)
                    return update_info
                except json.JSONDecodeError as e:
                    return {'error': f'JSON-Parse-Fehler: {e}'}
            else:
                return {'error': f'Update-Check fehlgeschlagen: {result.stderr}'}
        except Exception as e:
            return {'error': str(e)}
    
    def perform_update(self):
        """Führt das Update mit professionellem Update-System durch"""
        if self.update_in_progress:
            return {'error': 'Update bereits in Bearbeitung'}
        
        self.update_in_progress = True
        
        try:
            # Verwende das neue professionelle Update-System
            update_script = os.path.join(os.path.dirname(__file__), 'update_system.py')
            
            if not os.path.exists(update_script):
                return {'error': 'Update-Skript nicht gefunden'}
            
            # Prüfe ob wir bereits als root laufen
            if os.geteuid() == 0:
                # Als root: Direkt ausführen
                cmd = [sys.executable, update_script, 'update']
                print(f"Führe Update aus als root: {' '.join(cmd)}")
            else:
                # Nicht als root: Mit sudo ausführen
                # Finde sudo-Pfad
                sudo_paths = ['/usr/bin/sudo', '/bin/sudo', '/sbin/sudo']
                sudo_path = None
                
                for path in sudo_paths:
                    if os.path.exists(path):
                        sudo_path = path
                        break
                
                if sudo_path:
                    cmd = [sudo_path, sys.executable, update_script, 'update']
                    print(f"Führe Update aus mit sudo: {' '.join(cmd)}")
                else:
                    # Fallback: Versuche sudo über PATH zu finden
                    cmd = ['sudo', sys.executable, update_script, 'update']
                    print(f"Führe Update aus mit sudo (PATH): {' '.join(cmd)}")
            
            # Führe das Update aus
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            # Logge die Ausgabe für Debugging
            print(f"Update-Skript Return Code: {result.returncode}")
            print(f"Update-Skript Ausgabe: {result.stdout}")
            if result.stderr:
                print(f"Update-Skript Fehler: {result.stderr}")
            
            if result.returncode == 0:
                # Prüfe ob wirklich ein Update durchgeführt wurde
                if "System ist bereits aktuell" in result.stdout:
                    return {'success': True, 'message': 'System ist bereits aktuell'}
                elif "Update erfolgreich" in result.stdout or "Installation abgeschlossen" in result.stdout:
                    return {'success': True, 'message': 'Update erfolgreich abgeschlossen'}
                else:
                    return {'success': True, 'message': 'Update durchgeführt - siehe Logs für Details'}
            else:
                # Detaillierte Fehleranalyse
                error_msg = result.stderr if result.stderr else result.stdout
                
                if "Permission denied" in error_msg:
                    return {'error': 'Berechtigungsfehler: Update benötigt Root-Rechte. Bitte führen Sie das Update manuell mit "sudo python3 update_system.py update" aus.'}
                elif "No such file or directory" in error_msg:
                    return {'error': 'Datei nicht gefunden: Update-Skript oder Abhängigkeiten fehlen.'}
                elif "Timeout" in error_msg:
                    return {'error': 'Update-Timeout: Das Update dauerte zu lange.'}
                else:
                    return {'error': f'Update fehlgeschlagen: {error_msg}'}
                    
        except subprocess.TimeoutExpired:
            return {'error': 'Update-Timeout: Das Update dauerte zu lange (über 5 Minuten)'}
        except FileNotFoundError as e:
            return {'error': f'Datei nicht gefunden: {str(e)}'}
        except PermissionError as e:
            return {'error': f'Berechtigungsfehler: {str(e)}'}
        except Exception as e:
            return {'error': f'Unerwarteter Fehler: {str(e)}'}
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

# USB Device Manager API Endpoints
@app.route('/api/devices')
def api_get_devices():
    """API-Endpoint für alle USB-Geräte"""
    return jsonify(device_manager.get_all_devices())

@app.route('/api/devices/types')
def api_get_device_types():
    """API-Endpoint für verfügbare Gerätetypen"""
    return jsonify(device_manager.device_types)

@app.route('/api/devices/available')
def api_get_available_devices():
    """API-Endpoint für verfügbare USB-Geräte"""
    return jsonify(device_manager.get_available_usb_devices())

@app.route('/api/devices', methods=['POST'])
def api_add_device():
    """API-Endpoint zum Hinzufügen eines Geräts"""
    data = request.get_json()
    
    required_fields = ['device_type', 'model', 'device_info']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Fehlendes Feld: {field}'}), 400
    
    try:
        device = device_manager.add_device(
            device_type=data['device_type'],
            model=data['model'],
            device_info=data['device_info'],
            custom_name=data.get('custom_name', '')
        )
        return jsonify(device)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/devices/<device_id>', methods=['DELETE'])
def api_remove_device(device_id):
    """API-Endpoint zum Entfernen eines Geräts"""
    try:
        success = device_manager.remove_device(device_id)
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Gerät nicht gefunden'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/devices/<device_id>/connect', methods=['POST'])
def api_connect_device(device_id):
    """API-Endpoint zum Verbinden eines Geräts"""
    try:
        success = device_manager.connect_device(device_id)
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Gerät nicht gefunden'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/devices/<device_id>/disconnect', methods=['POST'])
def api_disconnect_device(device_id):
    """API-Endpoint zum Trennen eines Geräts"""
    try:
        success = device_manager.disconnect_device(device_id)
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Gerät nicht gefunden'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/devices/<device_id>/test', methods=['POST'])
def api_test_device(device_id):
    """API-Endpoint zum Testen eines Geräts"""
    data = request.get_json()
    test_type = data.get('test_type', 'test_print')
    
    try:
        result = device_manager.test_device(device_id, test_type)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/devices/<device_id>/settings', methods=['PUT'])
def api_update_device_settings(device_id):
    """API-Endpoint zum Aktualisieren der Geräteeinstellungen"""
    data = request.get_json()
    
    try:
        success = device_manager.update_device_settings(device_id, data)
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Gerät nicht gefunden'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/devices/<device_id>/status')
def api_get_device_status(device_id):
    """API-Endpoint für Gerätestatus"""
    try:
        status = device_manager.get_device_status(device_id)
        if status:
            return jsonify(status)
        else:
            return jsonify({'error': 'Gerät nicht gefunden'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scanner/status')
def api_get_scanner_status():
    """API-Endpoint für Datalogic Touch 65 Scanner-Status"""
    try:
        status = device_manager.datalogic_scanner.get_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scanner/connect', methods=['POST'])
def api_connect_scanner():
    """API-Endpoint zum Verbinden des Datalogic Touch 65 Scanners"""
    try:
        success = device_manager.datalogic_scanner.connect()
        if success:
            return jsonify({'success': True, 'message': 'Scanner erfolgreich verbunden'})
        else:
            return jsonify({'success': False, 'error': 'Scanner-Verbindung fehlgeschlagen'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scanner/disconnect', methods=['POST'])
def api_disconnect_scanner():
    """API-Endpoint zum Trennen des Datalogic Touch 65 Scanners"""
    try:
        device_manager.datalogic_scanner.disconnect()
        return jsonify({'success': True, 'message': 'Scanner getrennt'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Konfiguration aus Umgebungsvariablen
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8080))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    print(f"DeviceBox v{devicebox.version} startet auf {host}:{port}")
    app.run(host=host, port=port, debug=debug)
