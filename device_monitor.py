#!/usr/bin/env python3
"""
Device Monitor für DeviceBox
Überwacht Systemstatus des Raspberry Pi
"""

import os
import psutil
import subprocess
from datetime import datetime

class DeviceMonitor:
    def __init__(self):
        pass
    
    def get_device_status(self):
        """Vollständigen Gerätestatus abrufen"""
        try:
            status = {
                'timestamp': datetime.now().isoformat(),
                'system': self._get_system_info(),
                'cpu': self._get_cpu_info(),
                'memory': self._get_memory_info(),
                'disk': self._get_disk_info(),
                'network': self._get_network_info(),
                'temperature': self._get_temperature(),
                'uptime': self._get_uptime(),
                'services': self._get_service_status()
            }
            return status
        except Exception as e:
            return {'error': str(e)}
    
    def _get_system_info(self):
        """System-Informationen abrufen"""
        try:
            return {
                'hostname': os.uname().nodename,
                'platform': os.uname().sysname,
                'release': os.uname().release,
                'version': os.uname().version,
                'machine': os.uname().machine
            }
        except:
            return {'error': 'System-Info nicht verfügbar'}
    
    def _get_cpu_info(self):
        """CPU-Informationen abrufen"""
        try:
            return {
                'usage_percent': psutil.cpu_percent(interval=1),
                'count': psutil.cpu_count(),
                'frequency': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
                'load_avg': os.getloadavg() if hasattr(os, 'getloadavg') else None
            }
        except:
            return {'error': 'CPU-Info nicht verfügbar'}
    
    def _get_memory_info(self):
        """Speicher-Informationen abrufen"""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            return {
                'total': memory.total,
                'available': memory.available,
                'used': memory.used,
                'free': memory.free,
                'usage_percent': memory.percent,
                'swap_total': swap.total,
                'swap_used': swap.used,
                'swap_free': swap.free,
                'swap_percent': swap.percent
            }
        except:
            return {'error': 'Speicher-Info nicht verfügbar'}
    
    def _get_disk_info(self):
        """Festplatten-Informationen abrufen"""
        try:
            disk_usage = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            return {
                'total': disk_usage.total,
                'used': disk_usage.used,
                'free': disk_usage.free,
                'usage_percent': (disk_usage.used / disk_usage.total) * 100,
                'read_bytes': disk_io.read_bytes if disk_io else 0,
                'write_bytes': disk_io.write_bytes if disk_io else 0,
                'read_count': disk_io.read_count if disk_io else 0,
                'write_count': disk_io.write_count if disk_io else 0
            }
        except:
            return {'error': 'Festplatten-Info nicht verfügbar'}
    
    def _get_network_info(self):
        """Netzwerk-Informationen abrufen"""
        try:
            network_io = psutil.net_io_counters()
            network_connections = len(psutil.net_connections())
            
            return {
                'bytes_sent': network_io.bytes_sent,
                'bytes_recv': network_io.bytes_recv,
                'packets_sent': network_io.packets_sent,
                'packets_recv': network_io.packets_recv,
                'connections': network_connections
            }
        except:
            return {'error': 'Netzwerk-Info nicht verfügbar'}
    
    def _get_temperature(self):
        """CPU-Temperatur abrufen (Raspberry Pi spezifisch)"""
        try:
            # Versuche verschiedene Temperatur-Pfade
            temp_paths = [
                '/sys/class/thermal/thermal_zone0/temp',
                '/sys/class/hwmon/hwmon0/temp1_input',
                '/sys/devices/virtual/thermal/thermal_zone0/temp'
            ]
            
            for temp_path in temp_paths:
                if os.path.exists(temp_path):
                    with open(temp_path, 'r') as f:
                        temp_millicelsius = int(f.read().strip())
                        temp_celsius = temp_millicelsius / 1000.0
                        return {
                            'cpu_temp': temp_celsius,
                            'unit': 'celsius'
                        }
            
            return {'error': 'Temperatur-Sensor nicht gefunden'}
        except:
            return {'error': 'Temperatur nicht verfügbar'}
    
    def _get_uptime(self):
        """System-Uptime abrufen"""
        try:
            uptime_seconds = int(psutil.boot_time())
            uptime_datetime = datetime.fromtimestamp(uptime_seconds)
            uptime_delta = datetime.now() - uptime_datetime
            
            return {
                'boot_time': uptime_datetime.isoformat(),
                'uptime_seconds': int(uptime_delta.total_seconds()),
                'uptime_days': uptime_delta.days,
                'uptime_hours': uptime_delta.seconds // 3600,
                'uptime_minutes': (uptime_delta.seconds % 3600) // 60
            }
        except:
            return {'error': 'Uptime nicht verfügbar'}
    
    def _get_service_status(self):
        """Status wichtiger Services abrufen"""
        try:
            services = ['devicebox', 'ssh', 'nginx', 'apache2']
            service_status = {}
            
            for service in services:
                try:
                    result = subprocess.run(['systemctl', 'is-active', service], 
                                          capture_output=True, text=True, timeout=5)
                    service_status[service] = {
                        'status': result.stdout.strip(),
                        'active': result.stdout.strip() == 'active'
                    }
                except:
                    service_status[service] = {
                        'status': 'unknown',
                        'active': False
                    }
            
            return service_status
        except:
            return {'error': 'Service-Status nicht verfügbar'}
