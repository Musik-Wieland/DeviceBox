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
                'models': ['Brother HL-L2340DW', 'HP LaserJet', 'Canon PIXMA'],
                'features': ['test_print']
            },
            'label_printer': {
                'name': 'Label-Printer',
                'models': ['Brother QL-700', 'Brother QL-800', 'Zebra ZD420'],
                'features': ['test_print', 'label_size']
            },
            'shipping_printer': {
                'name': 'Versandlabel-Printer',
                'models': ['Dymo LabelWriter', 'Brother QL-1100'],
                'features': ['test_print']
            },
            'barcode_scanner': {
                'name': 'Barcode-Scanner',
                'models': ['Datalogic Touch 65', 'Honeywell Voyager', 'Zebra DS2208'],
                'features': ['test_scan']
            },
            'receipt_printer': {
                'name': 'Bondrucker',
                'models': ['Epson TM-T20II', 'Epson TM-T88VI', 'Star TSP143'],
                'features': ['test_print']
            },
            'card_reader': {
                'name': 'EC-Kartengerät',
                'models': ['Ingenico Move/3500', 'Verifone VX520', 'PAX A920'],
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
        
        # USB-Geräte über lsusb ermitteln (Raspberry Pi)
        try:
            result = subprocess.run(['lsusb'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line and 'Bus' in line:
                        parts = line.split()
                        if len(parts) >= 6:
                            bus = parts[1]
                            device_id = parts[3].rstrip(':')
                            vendor_product = parts[5]
                            description = ' '.join(parts[6:]) if len(parts) > 6 else ''
                            
                            # Filtere System-Geräte heraus
                            if self.is_system_device(description, vendor_product):
                                continue
                            
                            # Extrahiere Hersteller aus der Beschreibung
                            manufacturer = self.extract_manufacturer(description)
                            
                            # Erkenne Gerätetyp
                            device_type = self.detect_device_type(description, vendor_product)
                            
                            # Prüfe ob es ein interessantes Gerät ist
                            if device_type != 'unknown' or self.is_interesting_device(description, vendor_product):
                                devices.append({
                                    'bus': bus,
                                    'device_id': device_id,
                                    'vendor_product': vendor_product,
                                    'description': description,
                                    'manufacturer': manufacturer,
                                    'type': 'usb',
                                    'device_type': device_type
                                })
        except Exception as e:
            print(f"Fehler beim Ermitteln der USB-Geräte: {e}")
        
        # Serielle Geräte ermitteln (nur echte Geräte, keine System-Ports)
        try:
            serial_ports = serial.tools.list_ports.comports()
            for port in serial_ports:
                # Filtere System-Ports heraus
                if self.is_system_serial_port(port.device):
                    continue
                    
                devices.append({
                    'port': port.device,
                    'description': port.description or 'Serielles Gerät',
                    'manufacturer': port.manufacturer,
                    'serial_number': port.serial_number,
                    'type': 'serial'
                })
        except Exception as e:
            print(f"Fehler beim Ermitteln der seriellen Geräte: {e}")
        
        return devices
    
    def is_system_device(self, description: str, vendor_product: str) -> bool:
        """Prüft ob es sich um ein System-Gerät handelt"""
        system_keywords = [
            'root hub', 'hub', 'ethernet', 'wifi', 'bluetooth', 'camera',
            'keyboard', 'mouse', 'audio', 'mass storage', 'usb hub'
        ]
        
        # Spezielle System-Vendor-IDs
        system_vendors = [
            '1d6b:0002',  # Linux Foundation 2.0 root hub
            '1d6b:0003',  # Linux Foundation 3.0 root hub
        ]
        
        description_lower = description.lower()
        for keyword in system_keywords:
            if keyword in description_lower:
                return True
        
        # Prüfe Vendor-IDs
        if vendor_product in system_vendors:
            return True
            
        return False
    
    def is_system_serial_port(self, port: str) -> bool:
        """Prüft ob es sich um einen System-Serial-Port handelt"""
        system_ports = [
            '/dev/ttyAMA0', '/dev/ttyAMA1', '/dev/ttyAMA2', '/dev/ttyAMA3',
            '/dev/ttyAMA4', '/dev/ttyAMA5', '/dev/ttyAMA6', '/dev/ttyAMA7',
            '/dev/ttyAMA8', '/dev/ttyAMA9', '/dev/ttyAMA10', '/dev/ttyAMA11',
            '/dev/ttyAMA12', '/dev/ttyAMA13', '/dev/ttyAMA14', '/dev/ttyAMA15',
            '/dev/ttyS0', '/dev/ttyS1', '/dev/ttyS2', '/dev/ttyS3',
            '/dev/serial0', '/dev/serial1', '/dev/serial2',
            '/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyUSB2', '/dev/ttyUSB3',
            '/dev/ttyUSB4', '/dev/ttyUSB5', '/dev/ttyUSB6', '/dev/ttyUSB7',
            '/dev/ttyUSB8', '/dev/ttyUSB9', '/dev/ttyUSB10', '/dev/ttyUSB11',
            '/dev/ttyUSB12', '/dev/ttyUSB13', '/dev/ttyUSB14', '/dev/ttyUSB15',
            '/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyACM2', '/dev/ttyACM3',
            '/dev/ttyACM4', '/dev/ttyACM5', '/dev/ttyACM6', '/dev/ttyACM7',
            '/dev/ttyACM8', '/dev/ttyACM9', '/dev/ttyACM10', '/dev/ttyACM11',
            '/dev/ttyACM12', '/dev/ttyACM13', '/dev/ttyACM14', '/dev/ttyACM15'
        ]
        
        return port in system_ports
    
    def detect_device_type(self, description: str, vendor_product: str) -> str:
        """Erkennt den Gerätetyp basierend auf Beschreibung und Vendor/Product ID"""
        description_lower = description.lower()
        
        # Barcode Scanner
        if 'barcode' in description_lower or 'scanner' in description_lower:
            return 'barcode_scanner'
        
        # Drucker
        if 'printer' in description_lower or 'print' in description_lower:
            if 'label' in description_lower:
                return 'label_printer'
            elif 'receipt' in description_lower or 'bond' in description_lower:
                return 'receipt_printer'
            else:
                return 'printer'
        
        # EC-Kartengerät
        if 'card' in description_lower or 'payment' in description_lower:
            return 'card_reader'
        
        # Bekannte Vendor-IDs
        known_devices = {
            '05f9:2214': 'barcode_scanner',  # PSC Scanning Barcode Scanner
            '04b8:0202': 'receipt_printer',  # Epson Receipt Printer
            '04b8:0203': 'receipt_printer',  # Epson Receipt Printer
            '04f9:2040': 'printer',          # Brother Printer
        }
        
        if vendor_product in known_devices:
            return known_devices[vendor_product]
        
        return 'unknown'
    
    def is_interesting_device(self, description: str, vendor_product: str) -> bool:
        """Prüft ob es sich um ein interessantes Gerät handelt"""
        interesting_keywords = [
            'scanner', 'barcode', 'printer', 'card', 'payment', 'pos',
            'terminal', 'reader', 'scale', 'display', 'monitor'
        ]
        
        description_lower = description.lower()
        for keyword in interesting_keywords:
            if keyword in description_lower:
                return True
        
        # Bekannte interessante Vendor-IDs
        interesting_vendors = [
            '05f9',  # PSC Scanning
            '04b8',  # Epson
            '04f9',  # Brother
            '0bda',  # Realtek
            '1a2c',  # China Resource Semico
        ]
        
        vendor_id = vendor_product.split(':')[0]
        if vendor_id in interesting_vendors:
            return True
            
        return False
    
    def extract_manufacturer(self, description: str) -> str:
        """Extrahiert den Hersteller aus der Gerätebeschreibung"""
        description_lower = description.lower()
        
        if 'brother' in description_lower:
            return 'Brother'
        elif 'epson' in description_lower:
            return 'Epson'
        elif 'hp' in description_lower or 'hewlett' in description_lower:
            return 'HP'
        elif 'canon' in description_lower:
            return 'Canon'
        elif 'datalogic' in description_lower:
            return 'Datalogic'
        elif 'honeywell' in description_lower:
            return 'Honeywell'
        elif 'zebra' in description_lower:
            return 'Zebra'
        elif 'dymo' in description_lower:
            return 'Dymo'
        elif 'star' in description_lower:
            return 'Star'
        elif 'ingenico' in description_lower:
            return 'Ingenico'
        elif 'verifone' in description_lower:
            return 'Verifone'
        elif 'pax' in description_lower:
            return 'PAX'
        else:
            return 'Unbekannt'
    
    def detect_device_type(self, device_info: Dict) -> Optional[str]:
        """Erkennt den Gerätetyp basierend auf Beschreibung und Hersteller"""
        description = device_info.get('description', '').lower()
        manufacturer = device_info.get('manufacturer', '').lower()
        
        # Brother Geräte
        if 'brother' in description or 'brother' in manufacturer:
            if 'ql-' in description:
                return 'label_printer'
            elif 'hl-' in description or 'mfc-' in description:
                return 'printer'
        
        # Epson Geräte
        if 'epson' in description or 'epson' in manufacturer:
            if 'tm-t' in description:
                return 'receipt_printer'
            elif 'workforce' in description or 'expression' in description:
                return 'printer'
        
        # HP Geräte
        if 'hp' in description or 'hewlett' in description or 'hp' in manufacturer:
            if 'laserjet' in description or 'officejet' in description:
                return 'printer'
        
        # Canon Geräte
        if 'canon' in description or 'canon' in manufacturer:
            if 'pixma' in description or 'imageclass' in description:
                return 'printer'
        
        # Datalogic Scanner
        if 'datalogic' in description or 'datalogic' in manufacturer:
            return 'barcode_scanner'
        
        # Honeywell Scanner
        if 'honeywell' in description or 'honeywell' in manufacturer:
            if 'voyager' in description or 'granit' in description:
                return 'barcode_scanner'
        
        # Zebra Geräte
        if 'zebra' in description or 'zebra' in manufacturer:
            if 'zd' in description or 'zt' in description:
                return 'label_printer'
            elif 'ds' in description:
                return 'barcode_scanner'
        
        # Dymo Label-Drucker
        if 'dymo' in description or 'dymo' in manufacturer:
            return 'label_printer'
        
        # Star Bondrucker
        if 'star' in description or 'star' in manufacturer:
            if 'tsp' in description:
                return 'receipt_printer'
        
        # Ingenico EC-Kartengerät
        if 'ingenico' in description or 'ingenico' in manufacturer:
            return 'card_reader'
        
        # Verifone EC-Kartengerät
        if 'verifone' in description or 'verifone' in manufacturer:
            return 'card_reader'
        
        # PAX EC-Kartengerät
        if 'pax' in description or 'pax' in manufacturer:
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
                test_content = self.generate_test_content(device_type)
                
                # Versuche echten Druck basierend auf Gerätetyp
                if device_type == 'receipt_printer':
                    success = self.print_receipt(device, test_content)
                elif device_type == 'label_printer':
                    success = self.print_label(device, test_content)
                elif device_type == 'printer':
                    success = self.print_document(device, test_content)
                else:
                    success = self.print_generic(device, test_content)
                
                if success:
                    return {
                        'success': True,
                        'message': f'Testdruck erfolgreich für {device["name"]}',
                        'test_content': test_content
                    }
                else:
                    return {'success': False, 'error': 'Druckvorgang fehlgeschlagen'}
            else:
                return {'success': False, 'error': 'Gerät unterstützt keinen Drucktest'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def print_receipt(self, device: Dict, content: str) -> bool:
        """Druckt einen Beleg (ESC/POS)"""
        try:
            device_info = device['device_info']
            
            if device_info.get('type') == 'usb':
                # USB ESC/POS Drucker
                return self.print_usb_escpos(device_info, content)
            elif device_info.get('type') == 'serial':
                # Serieller ESC/POS Drucker
                return self.print_serial_escpos(device_info, content)
            else:
                return False
        except Exception as e:
            print(f"Fehler beim Belegdruck: {e}")
            return False
    
    def print_label(self, device: Dict, content: str) -> bool:
        """Druckt ein Etikett"""
        try:
            device_info = device['device_info']
            
            if device_info.get('type') == 'usb':
                # Brother QL-Serie oder ähnliche
                return self.print_usb_label(device_info, content)
            else:
                return False
        except Exception as e:
            print(f"Fehler beim Etikettdruck: {e}")
            return False
    
    def print_document(self, device: Dict, content: str) -> bool:
        """Druckt ein Dokument"""
        try:
            # Für normale Drucker verwenden wir CUPS
            return self.print_cups(device, content)
        except Exception as e:
            print(f"Fehler beim Dokumentdruck: {e}")
            return False
    
    def print_generic(self, device: Dict, content: str) -> bool:
        """Generischer Druckvorgang"""
        try:
            # Simuliere Druckvorgang
            time.sleep(2)
            return True
        except Exception as e:
            print(f"Fehler beim generischen Druck: {e}")
            return False
    
    def print_usb_escpos(self, device_info: Dict, content: str) -> bool:
        """Druckt über USB ESC/POS"""
        try:
            import usb.core
            import usb.util
            
            # ESC/POS Befehle
            escpos_commands = [
                b'\x1B\x40',  # Initialize
                b'\x1B\x61\x01',  # Center align
                content.encode('utf-8'),
                b'\x0A\x0A\x0A',  # Line feeds
                b'\x1D\x56\x00',  # Cut paper
            ]
            
            # Hier würde die tatsächliche USB-Kommunikation stattfinden
            # Für jetzt simulieren wir den Erfolg
            time.sleep(1)
            return True
            
        except Exception as e:
            print(f"USB ESC/POS Fehler: {e}")
            return False
    
    def print_serial_escpos(self, device_info: Dict, content: str) -> bool:
        """Druckt über serielle ESC/POS"""
        try:
            import serial
            
            port = device_info['port']
            
            # ESC/POS Befehle
            escpos_commands = [
                b'\x1B\x40',  # Initialize
                b'\x1B\x61\x01',  # Center align
                content.encode('utf-8'),
                b'\x0A\x0A\x0A',  # Line feeds
                b'\x1D\x56\x00',  # Cut paper
            ]
            
            # Hier würde die tatsächliche serielle Kommunikation stattfinden
            # Für jetzt simulieren wir den Erfolg
            time.sleep(1)
            return True
            
        except Exception as e:
            print(f"Serieller ESC/POS Fehler: {e}")
            return False
    
    def print_usb_label(self, device_info: Dict, content: str) -> bool:
        """Druckt über USB Label-Drucker"""
        try:
            # Brother QL-Serie oder ähnliche Label-Drucker
            # Hier würde die spezifische Label-Drucker-Kommunikation stattfinden
            time.sleep(1)
            return True
            
        except Exception as e:
            print(f"USB Label-Drucker Fehler: {e}")
            return False
    
    def print_cups(self, device: Dict, content: str) -> bool:
        """Druckt über CUPS (Common Unix Printing System)"""
        try:
            # Erstelle temporäre Datei
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(content)
                temp_file = f.name
            
            # Drucke über CUPS
            result = subprocess.run([
                'lp', '-d', 'default', temp_file
            ], capture_output=True, text=True)
            
            # Lösche temporäre Datei
            os.unlink(temp_file)
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"CUPS Druck Fehler: {e}")
            return False
    
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
