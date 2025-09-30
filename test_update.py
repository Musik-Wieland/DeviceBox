#!/usr/bin/env python3
"""
DeviceBox Update Test-Skript
Einfacher Test für das Update-System
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from auto_update import DeviceBoxAutoUpdater

def main():
    print("DeviceBox Update Test")
    print("=" * 30)
    
    updater = DeviceBoxAutoUpdater()
    
    # Test 1: Update-Check
    print("\n1. Update-Check:")
    try:
        result = updater.check_for_updates()
        if 'error' in result:
            print(f"   Fehler: {result['error']}")
        else:
            print(f"   Verfügbar: {result.get('available', False)}")
            print(f"   Nachricht: {result.get('message', 'N/A')}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Test 2: Update durchführen
    print("\n2. Update durchführen:")
    try:
        success = updater.update()
        print(f"   Erfolg: {success}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    print("\nTest abgeschlossen!")

if __name__ == '__main__':
    main()
