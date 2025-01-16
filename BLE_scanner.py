import asyncio
from bleak import BleakScanner

async def scan_ble_devices():
    print("Scanning for BLE devices...")
    devices = await BleakScanner.discover()
    if devices:
        print("Found devices:")
        for i, device in enumerate(devices, start=1):
            if device.name != None:
                print(f"{i}. Name: {device.name}, Address: {device.address}")
    else:
        print("No BLE devices found.")

if __name__ == "__main__":
    asyncio.run(scan_ble_devices())
