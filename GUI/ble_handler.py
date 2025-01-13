import threading
import asyncio
from bleak import BleakClient, BleakScanner

class BLEHandler:
    SERVICE_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
    CHARACTERISTIC_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"

    def __init__(self, text_area, archive_callback, data_buffer, graph_callback):
        self.text_area = text_area
        self.archive_callback = archive_callback
        self.data_buffer = data_buffer
        self.graph_callback = graph_callback
        self.client = None

    def connect(self, device_address):
        try:
            self.client = BleakClient(device_address)
            connected = self.client.connect()
            if connected:
                print(f"Connected to {device_address}")
                threading.Thread(target=self.run_ble_notifications, daemon=True).start()
                return True
            else:
                print(f"Failed to connect to {device_address}")
                return False
        except Exception as e:
            self.text_area.insert('end', f"Error: {e}\n")
            return False


    def run_ble_notifications(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.start_ble_notifications())

    async def start_ble_notifications(self):
        if self.client:
            try:
                async with self.client as client:
                    print(f"Connected to {client.address}")
                    await client.start_notify(self.CHARACTERISTIC_UUID, self.handle_ble_notification)
                    print(f"Subscribed to notifications for {self.CHARACTERISTIC_UUID}")
                    while True:
                        await asyncio.sleep(1)
            except Exception as e:
                print(f"Error during BLE notification subscription: {e}")


    def handle_ble_notification(self, sender, data):
        print(data)
        received = data.decode('utf-8').strip()
        self.text_area.insert('end', f"{received}\n")
        self.text_area.see('end')
        self.archive_callback(received)
        try:
            ax, ay, az, gx, gy, gz = map(float, received.split(','))
            self.data_buffer.append((ax, ay, az, gx, gy, gz))
            if self.graph_callback:
                self.graph_callback()
        except ValueError:
            pass

    async def stop_notifications(self):
        """Stop BLE notifications."""
        if self.client:
            await self.client.stop_notify(self.CHARACTERISTIC_UUID)
            print("Stopped notifications")

    async def disconnect(self):
        """Disconnect from the BLE device."""
        if self.client:
            try:
                # Stop receiving notifications
                await self.stop_notifications()

                # Disconnect from the BLE device
                await self.client.disconnect()
                print("Disconnected from the BLE device")
                self.client = None
            except Exception as e:
                print(f"Error during disconnect: {e}")
        else:
            print("No BLE client to disconnect.")


    async def scan_devices(self):
        devices = await BleakScanner.discover()
        return [(device.name, device.address) for device in devices]
