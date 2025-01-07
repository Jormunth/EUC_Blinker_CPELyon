import tkinter as tk
from tkinter import scrolledtext, ttk
import serial
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import deque

# Initialize global variables
data_buffer = deque(maxlen=100)  # To store N last data points (ax, ay, az, gx, gy, gz)

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

            # Parse the IMU data (ax, ay, az, gx, gy, gz)
            try:
                data_values = received.split(',')
                if len(data_values) == 6:
                    ax, ay, az, gx, gy, gz = map(float, data_values)
                    data_buffer.append((ax, ay, az, gx, gy, gz))  # Add new data to the buffer
                    if graph_enabled.get():
                        update_graph()
            except ValueError:
                pass  # Ignore invalid data

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

def update_graph():
    if not data_buffer:
        return  # Skip updating if no data is available

    # Update the IMU data plot
    x_vals = range(len(data_buffer))  # Use indices as the x-axis
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

    # Adjust axes limits
    ax1.relim()  # Recalculate limits
    ax1.autoscale_view()  # Autoscale axes based on data

    ax2.relim()  # Recalculate limits
    ax2.autoscale_view()  # Autoscale axes based on data

    canvas.draw()  # Redraw the canvas


def toggle_graphs():
    # Enable or disable graphs based on checkbox
    if graph_enabled.get():
        graph_frame.pack(fill=tk.BOTH, expand=True)
    else:
        graph_frame.pack_forget()

# Create the main Tkinter window
root = tk.Tk()
root.title("Serial Interface")

# Create the top frame for connection settings
settings_frame = tk.Frame(root)
settings_frame.pack(pady=10, fill=tk.X)

# Port selection
tk.Label(settings_frame, text="Port:").pack(side=tk.LEFT, padx=5)
port_combobox = ttk.Combobox(settings_frame, values=["/dev/ttyACM0", "/dev/ttyUSB0", "COM3"], width=15)
port_combobox.set("/dev/ttyUSB0")
port_combobox.pack(side=tk.LEFT, padx=5)

# Baudrate selection
tk.Label(settings_frame, text="Baudrate:").pack(side=tk.LEFT, padx=5)
baudrate_combobox = ttk.Combobox(settings_frame, values=["9600", "19200", "38400", "115200", "460800"], width=10)
baudrate_combobox.set("115200")
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

# Create the checkbox for enabling/disabling graphs
graph_enabled = tk.BooleanVar(value=False)
graph_checkbox = tk.Checkbutton(root, text="Enable IMU Graphs", variable=graph_enabled, command=toggle_graphs)
graph_checkbox.pack()

# Create a frame for the graphs (initially hidden)
graph_frame = tk.Frame(root)

# Create matplotlib figure and axis
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6, 6))

# Create plots for ax, ay, az, gx, gy, gz
ax_plot, = ax1.plot([], [], label='Ax', color='r')
ay_plot, = ax1.plot([], [], label='Ay', color='g')
az_plot, = ax1.plot([], [], label='Az', color='b')
gx_plot, = ax2.plot([], [], label='Gx', color='r')
gy_plot, = ax2.plot([], [], label='Gy', color='g')
gz_plot, = ax2.plot([], [], label='Gz', color='b')

# Set labels and titles
ax1.set_title("Accelerometer Data (Ax, Ay, Az)")
ax1.set_ylabel("Acceleration (g)")
ax2.set_title("Gyroscope Data (Gx, Gy, Gz)")
ax2.set_ylabel("Angular velocity (°/s)")
ax2.set_xlabel("Time (s)")

# Add legend
ax1.legend()
ax2.legend()

# Create canvas to display the plot in Tkinter
canvas = FigureCanvasTkAgg(fig, master=graph_frame)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# Run the Tkinter event loop
root.mainloop()

# Close the serial connection when the program exits
if 'ser' in globals() and ser:
    ser.close()
