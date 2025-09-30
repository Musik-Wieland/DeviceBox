#!/usr/bin/env python3
"""
DeviceBox USB Device Manager
Verwaltet USB-Geräte wie Drucker, Scanner und EC-Kartengeräte
"""

import os
import json
import subprocess
import time
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any
import usb.core
import usb.util
import serial.tools.list_ports

class USBDeviceManager:
    def __init__(self, config_file: str = "/opt/devicebox/data/devices.json"):
        self.config_file = config_file
        self.devices = {}
        self.device_types = {
            'printer': {
                'name': 'Papierdrucker',
                'models': ['Brother HL-L2340DW'],
                'features': ['test_print']
            },
            'label_printer': {
                'name': 'Label-Printer',
                'models': ['Brother QL-700'],
                'features': ['test_print', 'label_size']
            },
            'shipping_printer': {
                'name': 'Versandlabel-Printer',
                'models': [],
                'features': ['test_print']
            },
            'barcode_scanner': {
                'name': 'Barcode-Scanner',
                'models': ['Datalogic Touch 65'],
                'features': ['test_scan']
            },
            'receipt_printer': {
                'name': 'Bondrucker',
                'models': ['Epson TM-T20II'],
                'features': ['test_print']
            },
            'card_reader': {
                'name': 'EC-Kartengerät',
                'models': ['Ingenico Move/3500'],
                'features': ['test_transaction']
            }
        }
        self.load_devices()
        self.start_device_monitoring()
    
    def load_devices(self):
        """Lädt gespeicherte Geräte aus der Konfigurationsdatei"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.devices = json.load(f)
            else:
                self.devices = {}
        except Exception as e:
            print(f"Fehler beim Laden der Geräte: {e}")
            self.devices = {}
    
    def save_devices(self):
        """Speichert Geräte in die Konfigurationsdatei"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.devices, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Fehler beim Speichern der Geräte: {e}")
    
    def get_available_usb_devices(self) -> List[Dict]:
        """Ermittelt alle verfügbaren USB-Geräte"""
        devices = []
        
        try:
            # USB-Geräte über lsusb ermitteln
            result = subprocess.run(['lsusb'], capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split()
                        if len(parts) >= 6:
                            bus = parts[1]
                            device_id = parts[3].rstrip(':')
                            vendor_product = parts[5]
                            description = ' '.join(parts[6:]) if len(parts) > 6 else ''
                            
                            devices.append({
                                'bus': bus,
                                'device_id': device_id,
                                'vendor_product': vendor_product,
                                'description': description,
                                'type': 'usb'
                            })
        except Exception as e:
            print(f"Fehler beim Ermitteln der USB-Geräte: {e}")
        
        # Serielle Geräte ermitteln
        try:
            serial_ports = serial.tools.list_ports.comports()
            for port in serial_ports:
                devices.append({
                    'port': port.device,
                    'description': port.description,
                    'manufacturer': port.manufacturer,
                    'serial_number': port.serial_number,
                    'type': 'serial'
                })
        except Exception as e:
            print(f"Fehler beim Ermitteln der seriellen Geräte: {e}")
        
        return devices
    
    def detect_device_type(self, device_info: Dict) -> Optional[str]:
        """Erkennt den Gerätetyp basierend auf Beschreibung und Hersteller"""
        description = device_info.get('description', '').lower()
        manufacturer = device_info.get('manufacturer', '').lower()
        
        # Brother Geräte
        if 'brother' in description or 'brother' in manufacturer:
            if 'ql-' in description:
                return 'label_printer'
            elif 'hl-' in description:
                return 'printer'
        
        # Epson Geräte
        if 'epson' in description or 'epson' in manufacturer:
            if 'tm-t' in description:
                return 'receipt_printer'
        
        # Datalogic Scanner
        if 'datalogic' in description or 'datalogic' in manufacturer:
            return 'barcode_scanner'
        
        # Ingenico EC-Kartengerät
        if 'ingenico' in description or 'ingenico' in manufacturer:
            return 'card_reader'
        
        return None
    
    def add_device(self, device_type: str, model: str, device_info: Dict, custom_name: str = "") -> Dict:
        """Fügt ein neues Gerät hinzu"""
        device_id = f"{device_type}_{len(self.devices) + 1}_{int(time.time())}"
        
        device = {
            'id': device_id,
            'type': device_type,
            'model': model,
            'name': custom_name or f"{self.device_types[device_type]['name']} ({model})",
            'device_info': device_info,
            'status': 'disconnected',
            'last_seen': None,
            'created_at': datetime.now().isoformat(),
            'settings': self.get_default_settings(device_type)
        }
        
        self.devices[device_id] = device
        self.save_devices()
        
        # Versuche Gerät zu verbinden
        self.connect_device(device_id)
        
        return device
    
    def get_default_settings(self, device_type: str) -> Dict:
        """Gibt die Standard-Einstellungen für einen Gerätetyp zurück"""
        settings = {
            'printer': {
                'paper_size': 'A4',
                'quality': 'normal',
                'color': False
            },
            'label_printer': {
                'label_size': '62x100',
                'quality': 'high',
                'cut_after_print': True
            },
            'shipping_printer': {
                'paper_size': 'A4',
                'quality': 'normal'
            },
            'barcode_scanner': {
                'scan_mode': 'continuous',
                'beep_enabled': True,
                'led_enabled': True
            },
            'receipt_printer': {
                'paper_width': '80mm',
                'quality': 'normal',
                'cut_after_print': True
            },
            'card_reader': {
                'timeout': 30,
                'currency': 'EUR',
                'test_amount': 1.00
            }
        }
        return settings.get(device_type, {})
    
    def connect_device(self, device_id: str) -> bool:
        """Versucht ein Gerät zu verbinden"""
        if device_id not in self.devices:
            return False
        
        device = self.devices[device_id]
        device_info = device['device_info']
        
        try:
            if device_info.get('type') == 'usb':
                # USB-Gerät verbinden
                bus = int(device_info['bus'])
                device_num = int(device_info['device_id'])
                
                # Hier würde die tatsächliche USB-Verbindung stattfinden
                device['status'] = 'connected'
                device['last_seen'] = datetime.now().isoformat()
                
            elif device_info.get('type') == 'serial':
                # Serielles Gerät verbinden
                port = device_info['port']
                
                # Hier würde die serielle Verbindung stattfinden
                device['status'] = 'connected'
                device['last_seen'] = datetime.now().isoformat()
            
            self.save_devices()
            return True
            
        except Exception as e:
            print(f"Fehler beim Verbinden des Geräts {device_id}: {e}")
            device['status'] = 'error'
            device['error'] = str(e)
            self.save_devices()
            return False
    
    def disconnect_device(self, device_id: str) -> bool:
        """Trennt ein Gerät"""
        if device_id not in self.devices:
            return False
        
        device = self.devices[device_id]
        device['status'] = 'disconnected'
        device['last_seen'] = None
        self.save_devices()
        return True
    
    def remove_device(self, device_id: str) -> bool:
        """Entfernt ein Gerät komplett"""
        if device_id in self.devices:
            del self.devices[device_id]
            self.save_devices()
            return True
        return False
    
    def test_device(self, device_id: str, test_type: str) -> Dict:
        """Führt einen Test für ein Gerät durch"""
        if device_id not in self.devices:
            return {'success': False, 'error': 'Gerät nicht gefunden'}
        
        device = self.devices[device_id]
        device_type = device['type']
        
        if device['status'] != 'connected':
            return {'success': False, 'error': 'Gerät nicht verbunden'}
        
        try:
            if test_type == 'test_print':
                return self.test_print(device_id)
            elif test_type == 'test_scan':
                return self.test_scan(device_id)
            elif test_type == 'test_transaction':
                return self.test_transaction(device_id)
            else:
                return {'success': False, 'error': 'Unbekannter Test-Typ'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_print(self, device_id: str) -> Dict:
        """Testet das Drucken"""
        device = self.devices[device_id]
        device_type = device['type']
        
        try:
            if device_type in ['printer', 'label_printer', 'shipping_printer', 'receipt_printer']:
                # Hier würde der tatsächliche Drucktest stattfinden
                test_content = self.generate_test_content(device_type)
                
                # Simuliere Druckvorgang
                time.sleep(2)
                
                return {
                    'success': True,
                    'message': f'Testdruck erfolgreich für {device["name"]}',
                    'test_content': test_content
                }
            else:
                return {'success': False, 'error': 'Gerät unterstützt keinen Drucktest'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_scan(self, device_id: str) -> Dict:
        """Testet das Barcode-Scannen"""
        device = self.devices[device_id]
        
        try:
            if device['type'] == 'barcode_scanner':
                # Hier würde der tatsächliche Scan-Test stattfinden
                # Simuliere Scan-Vorgang
                time.sleep(1)
                
                return {
                    'success': True,
                    'message': f'Barcode-Scan erfolgreich für {device["name"]}',
                    'scan_result': '1234567890123'
                }
            else:
                return {'success': False, 'error': 'Gerät ist kein Barcode-Scanner'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_transaction(self, device_id: str) -> Dict:
        """Testet eine EC-Karten-Transaktion"""
        device = self.devices[device_id]
        
        try:
            if device['type'] == 'card_reader':
                # Hier würde der tatsächliche Transaktionstest stattfinden
                # Simuliere Transaktions-Vorgang
                time.sleep(3)
                
                return {
                    'success': True,
                    'message': f'EC-Karten-Test erfolgreich für {device["name"]}',
                    'transaction_id': 'TXN123456789',
                    'amount': device['settings'].get('test_amount', 1.00)
                }
            else:
                return {'success': False, 'error': 'Gerät ist kein EC-Kartengerät'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def generate_test_content(self, device_type: str) -> str:
        """Generiert Testinhalt für verschiedene Druckertypen"""
        content = {
            'printer': """
DeviceBox Testdruck
==================

Datum: {date}
Zeit: {time}
Gerät: Papierdrucker

Dies ist ein Testdruck um die Funktionalität
des Druckers zu überprüfen.

DeviceBox USB Device Manager
            """,
            'label_printer': """
DeviceBox Label-Test
====================

Test-Label
Datum: {date}
Zeit: {time}

QR-Code: [QR: DeviceBox Test]
            """,
            'receipt_printer': """
DeviceBox Bondruck-Test
========================

Datum: {date}
Zeit: {time}

Artikel: Test-Artikel
Preis: 1,00 EUR

Vielen Dank!
            """,
            'shipping_printer': """
DeviceBox Versandlabel-Test
============================

Absender: Test Absender
Empfänger: Test Empfänger

Tracking: TEST123456789
            """
        }
        
        now = datetime.now()
        template = content.get(device_type, content['printer'])
        return template.format(
            date=now.strftime('%d.%m.%Y'),
            time=now.strftime('%H:%M:%S')
        )
    
    def update_device_settings(self, device_id: str, settings: Dict) -> bool:
        """Aktualisiert die Einstellungen eines Geräts"""
        if device_id in self.devices:
            self.devices[device_id]['settings'].update(settings)
            self.save_devices()
            return True
        return False
    
    def get_device_status(self, device_id: str) -> Dict:
        """Gibt den Status eines Geräts zurück"""
        if device_id in self.devices:
            device = self.devices[device_id]
            return {
                'id': device_id,
                'name': device['name'],
                'type': device['type'],
                'status': device['status'],
                'last_seen': device['last_seen'],
                'settings': device['settings']
            }
        return {}
    
    def get_all_devices(self) -> Dict:
        """Gibt alle Geräte zurück"""
        return self.devices
    
    def start_device_monitoring(self):
        """Startet das Monitoring der USB-Geräte"""
        def monitor_devices():
            while True:
                try:
                    self.check_device_status()
                    time.sleep(10)  # Alle 10 Sekunden prüfen
                except Exception as e:
                    print(f"Fehler beim Device-Monitoring: {e}")
                    time.sleep(30)
        
        monitor_thread = threading.Thread(target=monitor_devices, daemon=True)
        monitor_thread.start()
    
    def check_device_status(self):
        """Prüft den Status aller Geräte"""
        available_devices = self.get_available_usb_devices()
        
        for device_id, device in self.devices.items():
            # Hier würde die tatsächliche Status-Prüfung stattfinden
            # Für jetzt simulieren wir den Status
            if device['status'] == 'connected':
                device['last_seen'] = datetime.now().isoformat()
        
        self.save_devices()

# Globale Instanz
device_manager = USBDeviceManager()
