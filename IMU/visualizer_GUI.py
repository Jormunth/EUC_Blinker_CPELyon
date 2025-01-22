import tkinter as tk
from tkinter import scrolledtext, ttk
import asyncio
from bleak import BleakClient, BleakScanner
import threading
import serial
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import deque
import json
import csv
import os
from datetime import datetime

# Constants for BLE
SERVICE_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
CHARACTERISTIC_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"

# Variables for Serial
ser = None

# Initialize global variables
data_buffer = deque(maxlen=100)  # To store last data points (ax, ay, az, gx, gy, gz)

# Archive paths
archive_folder_json = "Archives_json"
archive_folder_csv = "Archives_csv"
os.makedirs(archive_folder_json, exist_ok=True)
os.makedirs(archive_folder_csv, exist_ok=True)

archive_filename_json = os.path.join(archive_folder_json, f"archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
archive_filename_csv = os.path.join(archive_folder_csv, f"archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

# Utility functions
def archive_data(data):
    timestamp = datetime.now().isoformat()
    archive_entry = {"timestamp": timestamp, "data": data}

    # JSON Archiving
    try:
        with open(archive_filename_json, "r") as file:
            archive = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        archive = []

    archive.append(archive_entry)
    with open(archive_filename_json, "w") as file:
        json.dump(archive, file, indent=4)

    # CSV Archiving
    file_exists = os.path.isfile(archive_filename_csv)
    with open(archive_filename_csv, "a", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)
        if not file_exists:
            csv_writer.writerow(["Timestamp", "Data"])
        csv_writer.writerow([timestamp] + data.split(','))

def update_graph():
    if not data_buffer:
        return

    x_vals = range(len(data_buffer))
    ax_vals = [data[0] for data in data_buffer]
    ay_vals = [data[1] for data in data_buffer]
    az_vals = [data[2] for data in data_buffer]
    gx_vals = [data[3] for data in data_buffer]
    gy_vals = [data[4] for data in data_buffer]
    gz_vals = [data[5] for data in data_buffer]

    ax_plot.set_data(x_vals, ax_vals)
    ay_plot.set_data(x_vals, ay_vals)
    az_plot.set_data(x_vals, az_vals)
    gx_plot.set_data(x_vals, gx_vals)
    gy_plot.set_data(x_vals, gy_vals)
    gz_plot.set_data(x_vals, gz_vals)

    ax1.relim()
    ax1.autoscale_view()
    ax2.relim()
    ax2.autoscale_view()
    canvas.draw()

# BLE Functions
async def log_ble_data(device_address):
    async with BleakClient(device_address) as client:
        await client.start_notify(CHARACTERISTIC_UUID, handle_ble_notification)
        while True:
            await asyncio.sleep(1)

def handle_ble_notification(sender, data):
    received = data.decode('utf-8').strip()
    text_area.insert(tk.END, f"{received}\n")
    text_area.see(tk.END)
    archive_data(received)
    try:
        ax, ay, az, gx, gy, gz = map(float, received.split(','))
        data_buffer.append((ax, ay, az, gx, gy, gz))
        if graph_enabled.get():
            update_graph()
    except ValueError:
        pass

async def scan_ble_devices():
    devices = await BleakScanner.discover()
    ble_device_combobox['values'] = [f"{device.name} ({device.address})" for device in devices]
    scan_text_area.delete(1.0, tk.END)
    for device in devices:
        scan_text_area.insert(tk.END, f"Name: {device.name}, Address: {device.address}\n")

# Serial Functions
def connect_serial():
    global ser
    try:
        port = port_combobox.get()
        baudrate = int(baudrate_combobox.get())
        ser = serial.Serial(port, baudrate, timeout=1)
        threading.Thread(target=read_serial_data, daemon=True).start()
        connect_button.config(state=tk.DISABLED)
        disconnect_button.config(state=tk.NORMAL)
    except serial.SerialException as e:
        text_area.insert(tk.END, f"Error: {e}\n")

def read_serial_data():
    while ser and ser.is_open:
        if ser.in_waiting > 0:
            received = ser.readline().decode('utf-8').strip()
            text_area.insert(tk.END, f"{received}\n")
            text_area.see(tk.END)

def disconnect_serial():
    global ser
    if ser:
        ser.close()
        ser = None
        connect_button.config(state=tk.NORMAL)
        disconnect_button.config(state=tk.DISABLED)

# Tkinter GUI
root = tk.Tk()
root.title("BLE and Serial Interface")

graph_enabled = tk.BooleanVar(value=False)

# Connection Type Selector
connection_frame = tk.Frame(root)
connection_frame.pack(pady=10)
connection_type = tk.StringVar(value="Serial")

tk.Label(connection_frame, text="Connection Type:").pack(side=tk.LEFT)
connection_dropdown = ttk.Combobox(connection_frame, values=["Serial", "BLE"], textvariable=connection_type, state="readonly")
connection_dropdown.pack(side=tk.LEFT)

# BLE Frame
ble_frame = tk.Frame(root)
ble_device_combobox = ttk.Combobox(ble_frame, width=30)
ble_device_combobox.pack(side=tk.LEFT, padx=5)
tk.Button(ble_frame, text="Scan BLE", command=lambda: asyncio.run(scan_ble_devices())).pack(side=tk.LEFT)
tk.Button(ble_frame, text="Connect BLE", command=lambda: asyncio.run(log_ble_data(ble_device_combobox.get().split('(')[-1].strip(')')))).pack(side=tk.LEFT)

# Serial Frame
serial_frame = tk.Frame(root)
tk.Label(serial_frame, text="Serial Port:").pack(side=tk.LEFT)
port_combobox = ttk.Combobox(serial_frame, values=["COM3", "/dev/ttyUSB0"], width=10)
port_combobox.pack(side=tk.LEFT, padx=5)
tk.Label(serial_frame, text="Baudrate:").pack(side=tk.LEFT)
baudrate_combobox = ttk.Combobox(serial_frame, values=["9600", "115200"], width=10)
baudrate_combobox.pack(side=tk.LEFT, padx=5)
connect_button = tk.Button(serial_frame, text="Connect Serial", command=connect_serial)
connect_button.pack(side=tk.LEFT)
disconnect_button = tk.Button(serial_frame, text="Disconnect Serial", command=disconnect_serial, state=tk.DISABLED)
disconnect_button.pack(side=tk.LEFT)

# Scrolled Text Area
text_area = scrolledtext.ScrolledText(root, height=10)
text_area.pack()

# Graph Toggle
graph_checkbox = tk.Checkbutton(root, text="Enable Graphs", variable=graph_enabled)
graph_checkbox.pack()

# Graph Area
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(5, 4))
ax_plot, = ax1.plot([], [], label="Ax")
ay_plot, = ax1.plot([], [], label="Ay")
az_plot, = ax1.plot([], [], label="Az")
gx_plot, = ax2.plot([], [], label="Gx")
gy_plot, = ax2.plot([], [], label="Gy")
gz_plot, = ax2.plot([], [], label="Gz")
ax1.legend()
ax2.legend()

canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack()

# Dynamically show/hide frames
def update_connection_view(*args):
    if connection_type.get() == "Serial":
        ble_frame.pack_forget()
        serial_frame.pack(pady=10)
    else:
        serial_frame.pack_forget()
        ble_frame.pack(pady=10)

connection_type.trace_add("write", update_connection_view)
update_connection_view()

root.mainloop()
