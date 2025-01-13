import tkinter as tk
from tkinter import ttk, scrolledtext
from ble_handler import BLEHandler
from serial_handler import SerialHandler
from graph_handler import GraphHandler
from archiver import Archiver
from collections import deque
import threading
import asyncio

class Application:
    def __init__(self, root):
        self.root = root
        self.root.title("BLE and Serial Interface")

        # Variables
        self.connection_type = tk.StringVar(value="Serial")
        self.data_buffer = deque(maxlen=100)
        self.graph_enabled = tk.BooleanVar(value=False)

        self.terminal_text_area = self.create_text_area()

        # Handlers
        self.archiver = Archiver()
        self.serial_handler = SerialHandler(self.terminal_text_area)
        self.ble_handler = BLEHandler(
            self.terminal_text_area,
            self.archiver.archive_data,
            self.data_buffer,
            self.update_graph if self.graph_enabled.get() else None,
        )
        self.graph_handler = GraphHandler(root, self.data_buffer)

        # UI
        self.create_ui()

    def create_ui(self):
        # Connection Selector
        connection_frame = tk.Frame(self.root)
        connection_frame.pack(pady=10)
        tk.Label(connection_frame, text="Connection Type:").pack(side=tk.LEFT)
        connection_dropdown = ttk.Combobox(connection_frame, values=["Serial", "BLE"], textvariable=self.connection_type, state="readonly")
        connection_dropdown.pack(side=tk.LEFT)
        self.connection_type.trace_add("write", self.update_connection_view)

        # BLE Frame
        self.ble_frame = tk.Frame(self.root)
        self.ble_device_combobox = ttk.Combobox(self.ble_frame, width=30)
        self.ble_device_combobox.pack(side=tk.LEFT, padx=5)
        tk.Button(self.ble_frame, text="Scan BLE", command=self.scan_ble_devices).pack(side=tk.LEFT)
        tk.Button(self.ble_frame, text="Connect BLE", command=self.connect_ble).pack(side=tk.LEFT)
        tk.Button(self.ble_frame, text="Disconnect BLE", command=self.disconnect_ble).pack(side=tk.LEFT)  # Add Disconnect BLE Button

        # Serial Frame
        self.serial_frame = tk.Frame(self.root)
        tk.Label(self.serial_frame, text="Serial Port:").pack(side=tk.LEFT)
        self.port_combobox = ttk.Combobox(self.serial_frame, values=["COM3", "/dev/ttyUSB0"], width=10)
        self.port_combobox.pack(side=tk.LEFT, padx=5)
        tk.Label(self.serial_frame, text="Baudrate:").pack(side=tk.LEFT)
        self.baudrate_combobox = ttk.Combobox(self.serial_frame, values=["9600", "115200"], width=10)
        self.baudrate_combobox.pack(side=tk.LEFT, padx=5)
        tk.Button(self.serial_frame, text="Connect Serial", command=self.connect_serial).pack(side=tk.LEFT)
        tk.Button(self.serial_frame, text="Disconnect Serial", command=self.disconnect_serial).pack(side=tk.LEFT)

        self.update_connection_view()

    def create_text_area(self):
        text_area = scrolledtext.ScrolledText(self.root, height=10)
        text_area.pack()
        return text_area

    def update_connection_view(self, *args):
        if self.connection_type.get() == "Serial":
            self.ble_frame.pack_forget()
            self.serial_frame.pack(pady=10)
        else:
            self.serial_frame.pack_forget()
            self.ble_frame.pack(pady=10)

    def connect_serial(self):
        port = self.port_combobox.get()
        baudrate = int(self.baudrate_combobox.get())
        self.serial_handler.connect(port, baudrate)

    def disconnect_serial(self):
        self.serial_handler.disconnect()

    def scan_ble_devices(self):
        # Scan for BLE devices and update the combobox
        threading.Thread(target=self._scan_ble_devices, daemon=True).start()

    def _scan_ble_devices(self):
        devices = asyncio.run(self.ble_handler.scan_devices())
        devices = [d for d in devices if d[0].count('-') < 4]
        self.device_map = {f"{name}": address for name, address in devices}
        # Update the BLE device combobox in the main thread
        self.root.after(0, self.update_ble_device_combobox)

    def update_ble_device_combobox(self):
        self.ble_device_combobox['values'] = list(self.device_map.keys())

    def connect_ble(self):
        # Retrieve the MAC address from the selected name
        selected_device = self.ble_device_combobox.get()
        if selected_device and selected_device in self.device_map:
            device_address = self.device_map[selected_device]
            print(device_address)
            threading.Thread(target=self._connect_ble, args=(device_address,), daemon=True).start()

    def _connect_ble(self, device_address):
        asyncio.run(self.ble_handler.connect(device_address))

    def disconnect_ble(self):
        """Disconnect from the BLE device"""
        self.ble_handler.disconnect()  # Calls the BLEHandler's disconnect method

if __name__ == "__main__":
    root = tk.Tk()
    app = Application(root)
    root.mainloop()
