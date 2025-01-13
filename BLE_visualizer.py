import asyncio
import tkinter as tk
from tkinter import ttk
from bleak import BleakScanner, BleakClient

class BLEApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BLE Device Manager")

        # Variables
        self.devices = {}
        self.selected_device = tk.StringVar()

        # UI Elements
        self.device_label = tk.Label(root, text="Périphériques BLE détectés :")
        self.device_label.pack(pady=5)

        self.device_dropdown = ttk.Combobox(root, textvariable=self.selected_device, state="readonly", width=40)
        self.device_dropdown.pack(pady=5)

        self.scan_button = tk.Button(root, text="Scanner", command=self.scan_devices)
        self.scan_button.pack(pady=5)

        self.connect_button = tk.Button(root, text="Connecter", command=self.connect_device)
        self.connect_button.pack(pady=5)

        self.status_label = tk.Label(root, text="Statut : En attente", fg="blue")
        self.status_label.pack(pady=10)

        self.data_label = tk.Label(root, text="Données BLE :")
        self.data_label.pack(pady=5)

        self.text_area = tk.Text(root, height=15, width=50, state="disabled")
        self.text_area.pack(padx=10, pady=5)

    async def async_scan_devices(self):
        self.status_label.config(text="Statut : Scan en cours...", fg="orange")
        self.devices = {}  # Reset devices

        try:
            found_devices = await BleakScanner.discover()
            for device in found_devices:
                if device.name.count('-') < 4:  # Filter by MAC address
                # if "ESP32_EUC" in device.name:  # Filter by name
                    self.devices[device.name] = device.address

            # Update dropdown
            self.device_dropdown['values'] = list(self.devices.keys())
            if self.devices:
                self.device_dropdown.set("Sélectionnez un périphérique")
                self.status_label.config(text=f"Statut : {len(self.devices)} périphérique(s) trouvé(s).", fg="green")
            else:
                self.device_dropdown.set("")
                self.status_label.config(text="Statut : Aucun périphérique trouvé.", fg="red")

        except Exception as e:
            self.status_label.config(text=f"Erreur : {e}", fg="red")

    def scan_devices(self):
        asyncio.run(self.async_scan_devices())

    async def async_connect_device(self):
        address = self.devices[self.selected_device.get()]
        if not address:
            self.status_label.config(text="Statut : Veuillez sélectionner un périphérique.", fg="red")
            return

        self.status_label.config(text=f"Statut : Connexion à {address}...", fg="orange")
        try:
            async with BleakClient(address) as client:
                self.status_label.config(text=f"Statut : Connecté à {address}", fg="green")

                # Enable notifications and display incoming data
                def handle_notification(sender, data):
                    self.text_area.config(state="normal")
                    self.text_area.insert(tk.END, f"Données : {data.decode('utf-8')}\n")
                    self.text_area.config(state="disabled")
                    self.text_area.see(tk.END)

                service_uuid = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
                char_uuid = "beb5483e-36e1-4688-b7f5-ea07361b26a8"

                await client.start_notify(char_uuid, handle_notification)
                self.status_label.config(text=f"Statut : Notifications activées pour {address}.", fg="blue")

                # Wait while notifications arrive (exit with window close)
                while True:
                    await asyncio.sleep(1)

        except Exception as e:
            self.status_label.config(text=f"Erreur : {e}", fg="red")

    def connect_device(self):
        asyncio.run(self.async_connect_device())

if __name__ == "__main__":
    root = tk.Tk()
    app = BLEApp(root)
    root.mainloop()
