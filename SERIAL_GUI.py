import tkinter as tk
from tkinter import scrolledtext, ttk
import serial
import threading

def send_data():
    data = entry.get()
    if data:
        ser.write(data.encode('utf-8'))  # Send data
        entry.delete(0, tk.END)  # Clear the input field

def read_data():
    while True:
        if ser.in_waiting > 0:
            received = ser.readline().decode('utf-8').strip()  # Read and decode
            if received.startswith('[2H'):
                text_area.delete(1.0, tk.END)
                received = received.replace('[2H', '')  # Remove ANSI escape codes
            text_area.insert(tk.END, f"{received}\n")
            text_area.see(tk.END)  # Auto-scroll to the bottom

def start_reading():
    global read_thread
    read_thread = threading.Thread(target=read_data, daemon=True)
    read_thread.start()

def connect_serial():
    global ser
    try:
        port = port_combobox.get()
        baudrate = int(baudrate_combobox.get())
        ser = serial.Serial(port, baudrate, timeout=1)
        start_reading()
        connect_button.config(state=tk.DISABLED)
        disconnect_button.config(state=tk.NORMAL)
    except serial.SerialException as e:
        text_area.insert(tk.END, f"Error: {e}\n")
        text_area.see(tk.END)

def disconnect_serial():
    global ser
    if ser:
        ser.close()
        ser = None
        connect_button.config(state=tk.NORMAL)
        disconnect_button.config(state=tk.DISABLED)
        text_area.insert(tk.END, "Disconnected from serial port.\n")
        text_area.see(tk.END)

# Create the main Tkinter window
root = tk.Tk()
root.title("Serial Interface")

# Create the top frame for connection settings
settings_frame = tk.Frame(root)
settings_frame.pack(pady=10, fill=tk.X)

# Port selection
tk.Label(settings_frame, text="Port:").pack(side=tk.LEFT, padx=5)
port_combobox = ttk.Combobox(settings_frame, values=["/dev/ttyACM0", "/dev/ttyUSB0", "COM3"], width=15)
port_combobox.set("/dev/ttyACM0")
port_combobox.pack(side=tk.LEFT, padx=5)

# Baudrate selection
tk.Label(settings_frame, text="Baudrate:").pack(side=tk.LEFT, padx=5)
baudrate_combobox = ttk.Combobox(settings_frame, values=["9600", "19200", "38400", "115200", "460800"], width=10)
baudrate_combobox.set("460800")
baudrate_combobox.pack(side=tk.LEFT, padx=5)

# Connect button
connect_button = tk.Button(settings_frame, text="Connect", command=connect_serial)
connect_button.pack(side=tk.LEFT, padx=10)

# Disconnect button
disconnect_button = tk.Button(settings_frame, text="Disconnect", command=disconnect_serial, state=tk.DISABLED)
disconnect_button.pack(side=tk.LEFT, padx=10)

# Create widgets for sending data
frame = tk.Frame(root)
frame.pack(pady=10, fill=tk.X)

entry = tk.Entry(frame, width=30)
entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

send_button = tk.Button(frame, text="Send", command=send_data)
send_button.pack(side=tk.LEFT)

# Create the resizable text area
text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD)
text_area.pack(pady=10, fill=tk.BOTH, expand=True)

# Run the Tkinter event loop
root.mainloop()

# Close the serial connection when the program exits
if 'ser' in globals() and ser:
    ser.close()
