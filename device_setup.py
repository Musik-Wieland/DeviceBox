#!/usr/bin/env python3
"""
DeviceBox Geräte-Setup
Installiert und konfiguriert spezifische Geräte für das DeviceBox System
"""

import os
import sys
import subprocess
import json
from typing import Dict, List

class DeviceSetup:
    def __init__(self):
        self.setup_log = []
        
    def log(self, message: str):
        """Loggt Setup-Nachrichten"""
        print(f"[SETUP] {message}")
        self.setup_log.append(message)
    
    def install_system_dependencies(self):
        """Installiert System-Abhängigkeiten für die Geräte"""
        self.log("Installiere System-Abhängigkeiten...")
        
        dependencies = [
            "cups",                    # Drucker-System
            "cups-client",            # CUPS Client
            "printer-driver-brlaser", # Brother Laser-Treiber
            "python3-pip",            # Python Package Manager
            "python3-dev",            # Python Development Headers
            "libusb-1.0-0-dev",       # USB Development Headers
            "libudev-dev",            # udev Development Headers
        ]
        
        for dep in dependencies:
            try:
                self.log(f"Installiere {dep}...")
                result = subprocess.run([
                    "sudo", "apt-get", "install", "-y", dep
                ], capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    self.log(f"✓ {dep} erfolgreich installiert")
                else:
                    self.log(f"✗ Fehler bei {dep}: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                self.log(f"✗ Timeout bei {dep}")
            except Exception as e:
                self.log(f"✗ Fehler bei {dep}: {str(e)}")
    
    def install_python_dependencies(self):
        """Installiert Python-Abhängigkeiten"""
        self.log("Installiere Python-Abhängigkeiten...")
        
        try:
            # Installiere aus requirements.txt
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
            ], capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                self.log("✓ Python-Abhängigkeiten erfolgreich installiert")
            else:
                self.log(f"✗ Fehler bei Python-Abhängigkeiten: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            self.log("✗ Timeout bei Python-Abhängigkeiten")
        except Exception as e:
            self.log(f"✗ Fehler bei Python-Abhängigkeiten: {str(e)}")
    
    def setup_cups_printers(self):
        """Konfiguriert CUPS für Brother HL-L2340DW"""
        self.log("Konfiguriere CUPS-Drucker...")
        
        try:
            # Starte CUPS-Service
            subprocess.run(["sudo", "systemctl", "start", "cups"], check=True)
            subprocess.run(["sudo", "systemctl", "enable", "cups"], check=True)
            
            # Füge Benutzer zur lp-Gruppe hinzu
            subprocess.run(["sudo", "usermod", "-a", "-G", "lp", os.getenv("USER", "pi")], check=True)
            
            self.log("✓ CUPS erfolgreich konfiguriert")
            self.log("  - CUPS Web-Interface: http://localhost:631")
            self.log("  - Brother HL-L2340DW kann über CUPS hinzugefügt werden")
            
        except Exception as e:
            self.log(f"✗ CUPS-Konfiguration fehlgeschlagen: {str(e)}")
    
    def setup_usb_permissions(self):
        """Konfiguriert USB-Berechtigungen für Geräte"""
        self.log("Konfiguriere USB-Berechtigungen...")
        
        try:
            # Erstelle udev-Regeln für die Geräte
            udev_rules = [
                "# Brother Drucker",
                'SUBSYSTEM=="usb", ATTRS{idVendor}=="04f9", MODE="0666", GROUP="plugdev"',
                "",
                "# Epson Bondrucker",
                'SUBSYSTEM=="usb", ATTRS{idVendor}=="04b8", MODE="0666", GROUP="plugdev"',
                "",
                "# Datalogic Scanner",
                'SUBSYSTEM=="usb", ATTRS{idVendor}=="05f9", MODE="0666", GROUP="plugdev"',
                "",
                "# Ingenico Payment Terminal",
                'SUBSYSTEM=="usb", ATTRS{idVendor}=="0bda", MODE="0666", GROUP="plugdev"',
            ]
            
            udev_file = "/etc/udev/rules.d/99-devicebox.rules"
            
            with open(udev_file, "w") as f:
                f.write("\n".join(udev_rules))
            
            # Lade udev-Regeln neu
            subprocess.run(["sudo", "udevadm", "control", "--reload-rules"], check=True)
            subprocess.run(["sudo", "udevadm", "trigger"], check=True)
            
            # Füge Benutzer zur plugdev-Gruppe hinzu
            subprocess.run(["sudo", "usermod", "-a", "-G", "plugdev", os.getenv("USER", "pi")], check=True)
            
            self.log("✓ USB-Berechtigungen erfolgreich konfiguriert")
            
        except Exception as e:
            self.log(f"✗ USB-Berechtigungen fehlgeschlagen: {str(e)}")
    
    def create_device_config(self):
        """Erstellt Standard-Gerätekonfiguration"""
        self.log("Erstelle Gerätekonfiguration...")
        
        try:
            config_dir = "/opt/devicebox/data"
            os.makedirs(config_dir, exist_ok=True)
            
            # Standard-Gerätekonfiguration
            default_devices = {
                "devices": {},
                "settings": {
                    "auto_detect": True,
                    "scan_interval": 10,
                    "log_level": "INFO"
                },
                "device_templates": {
                    "Brother HL-L2340DW": {
                        "type": "printer",
                        "library": "CUPS",
                        "default_settings": {
                            "paper_size": "A4",
                            "quality": "normal",
                            "color": False
                        }
                    },
                    "Brother QL-700": {
                        "type": "label_printer",
                        "library": "brother_ql",
                        "default_settings": {
                            "label_size": "62x100",
                            "quality": "high",
                            "cut_after_print": True
                        }
                    },
                    "Epson TM-T20II": {
                        "type": "receipt_printer",
                        "library": "python_escpos",
                        "default_settings": {
                            "paper_width": "80mm",
                            "quality": "normal",
                            "cut_after_print": True
                        }
                    },
                    "Datalogic Touch 65": {
                        "type": "barcode_scanner",
                        "library": "evdev",
                        "default_settings": {
                            "scan_mode": "continuous",
                            "beep_enabled": True,
                            "led_enabled": True
                        }
                    },
                    "Ingenico Move/3500": {
                        "type": "card_reader",
                        "library": "custom_sdk",
                        "default_settings": {
                            "timeout": 30,
                            "currency": "EUR",
                            "test_amount": 1.00
                        }
                    }
                }
            }
            
            config_file = os.path.join(config_dir, "device_config.json")
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(default_devices, f, indent=2, ensure_ascii=False)
            
            self.log("✓ Gerätekonfiguration erstellt")
            
        except Exception as e:
            self.log(f"✗ Gerätekonfiguration fehlgeschlagen: {str(e)}")
    
    def test_device_libraries(self):
        """Testet die verfügbaren Geräte-Bibliotheken"""
        self.log("Teste Geräte-Bibliotheken...")
        
        libraries = {
            "brother_ql": "Brother QL Label-Drucker",
            "python_escpos": "ESC/POS Bondrucker",
            "cups": "CUPS Drucker-System",
            "evdev": "Barcode-Scanner",
            "PIL": "Bildverarbeitung für Labels"
        }
        
        for lib, description in libraries.items():
            try:
                if lib == "brother_ql":
                    from brother_ql.conversion import convert
                    from brother_ql.backends.helpers import send
                    from brother_ql.raster import BrotherQLRaster
                elif lib == "python_escpos":
                    from escpos.printer import Usb
                elif lib == "cups":
                    import cups
                elif lib == "evdev":
                    import evdev
                elif lib == "PIL":
                    from PIL import Image
                
                self.log(f"✓ {lib} ({description}) verfügbar")
                
            except ImportError:
                self.log(f"✗ {lib} ({description}) nicht verfügbar")
    
    def run_full_setup(self):
        """Führt das vollständige Setup durch"""
        self.log("=== DeviceBox Geräte-Setup ===")
        
        try:
            self.install_system_dependencies()
            self.install_python_dependencies()
            self.setup_cups_printers()
            self.setup_usb_permissions()
            self.create_device_config()
            self.test_device_libraries()
            
            self.log("=== Setup abgeschlossen ===")
            self.log("")
            self.log("Nächste Schritte:")
            self.log("1. Geräte anschließen")
            self.log("2. DeviceBox neu starten: sudo systemctl restart devicebox")
            self.log("3. Weboberfläche öffnen und Geräte konfigurieren")
            self.log("")
            self.log("CUPS Web-Interface: http://localhost:631")
            self.log("DeviceBox Web-Interface: http://[IP-Adresse]")
            
        except Exception as e:
            self.log(f"✗ Setup fehlgeschlagen: {str(e)}")
            return False
        
        return True

if __name__ == "__main__":
    setup = DeviceSetup()
    success = setup.run_full_setup()
    sys.exit(0 if success else 1)
