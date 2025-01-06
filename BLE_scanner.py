import re
from bleak import BleakScanner

async def scan_ble_devices():
    print("Scan des périphériques BLE en cours...")
    devices = await BleakScanner.discover()
    if not devices:
        print("Aucun périphérique détecté.")
    else:
        print(f"{len(devices)} périphérique(s) détecté(s) :")
        for device in devices:
            name = device.name
            if "ESP32_EUC" in name :  # Vérifie s'il contient des lettres
                print(f"Nom : {name}, Adresse MAC : {device.address}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(scan_ble_devices())
