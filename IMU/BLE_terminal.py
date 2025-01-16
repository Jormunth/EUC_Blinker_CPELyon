import asyncio
from bleak import BleakClient

# Replace with the hardcoded BLE address
TOF_ADDRESS = "24:62:AB:F4:F4:7E"
IMU_ADDRESS_ = "F8:B3:B7:22:2E:3A"
DEVICE_ADDRESS = TOF_ADDRESS  # Replace with your BLE device address
CHARACTERISTIC_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"  # Replace with the correct characteristic UUID

async def connect_and_listen(address):
    try:
        print(f"[CONNEXION] Connecting to BLE device at address {address}...")
        async with BleakClient(address) as client:
            if client.is_connected:
                print(f"[CONNEXION] Successfully connected to {address}")

                # Define the notification handler
                def handle_notification(sender, data):
                    print(f"[NOTIFICATION] Data received: {data.decode('utf-8', errors='ignore')}")

                # Start receiving notifications from the given characteristic UUID
                await client.start_notify(CHARACTERISTIC_UUID, handle_notification)

                # Keep the connection open to receive notifications
                while client.is_connected:
                    await asyncio.sleep(1)  # Sleep to keep the event loop active

                print(f"[CONNEXION] Notifications stopped for {address}.")
            else:
                print(f"[CONNEXION] Failed to connect to {address}.")
    except Exception as e:
        print(f"[CONNEXION] Error while connecting: {e}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(connect_and_listen(DEVICE_ADDRESS))
