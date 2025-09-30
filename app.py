#!/usr/bin/env python3
"""
DeviceBox - Raspberry Pi Web Interface
Hauptanwendung mit Flask Backend
"""

import os
import json
import subprocess
import psutil
import requests
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from update_manager import UpdateManager
from device_monitor import DeviceMonitor

app = Flask(__name__)
update_manager = UpdateManager()
device_monitor = DeviceMonitor()

@app.route('/')
def index():
    """Hauptseite der Web-Oberfläche"""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """API Endpoint für Gerätestatus"""
    try:
        status = device_monitor.get_device_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/version')
def get_version():
    """API Endpoint für aktuelle Version"""
    try:
        version_info = update_manager.get_current_version()
        return jsonify(version_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/check-updates')
def check_updates():
    """API Endpoint für Update-Check"""
    try:
        update_info = update_manager.check_for_updates()
        return jsonify(update_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/update', methods=['POST'])
def perform_update():
    """API Endpoint für Update-Durchführung"""
    try:
        result = update_manager.perform_update()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reboot', methods=['POST'])
def reboot_system():
    """API Endpoint für System-Neustart"""
    try:
        subprocess.run(['sudo', 'reboot'], check=True)
        return jsonify({'status': 'success', 'message': 'System wird neu gestartet'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Für Entwicklung
    app.run(host='0.0.0.0', port=5000, debug=False)
