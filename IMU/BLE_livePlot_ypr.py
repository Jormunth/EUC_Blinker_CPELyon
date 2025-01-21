import asyncio
from bleak import BleakClient
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import deque

# Replace with your BLE device details
DEVICE_ADDRESS = "CC:DB:A7:9E:DC:FA"
CHARACTERISTIC_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"

# Data buffer for live plotting
buffer_size = 100
data_buffer = deque([0] * buffer_size, maxlen=buffer_size)

# BLE notification handler
def handle_notification(sender, data):
    try:
        # Parse and store the data
        value = float(data.decode('utf-8', errors='ignore').strip())
        data_buffer.append(value)
    except ValueError:
        print(f"[NOTIFICATION] Received non-numeric data: {data}")

# Async BLE connection
async def connect_and_listen(address):
    print(f"[CONNEXION] Connecting to BLE device at address {address}...")
    async with BleakClient(address) as client:
        if client.is_connected:
            print(f"[CONNEXION] Successfully connected to {address}.")
            await client.start_notify(CHARACTERISTIC_UUID, handle_notification)

            # Keep the connection open
            while client.is_connected:
                await asyncio.sleep(1)

# Plot update function
def update_plot(frame):
    ax.clear()
    ax.plot(data_buffer, label="Sensor Data")
    ax.set_title("Live Sensor Data")
    ax.set_xlabel("Time (arbitrary units)")
    ax.set_ylabel("Value")
    ax.legend(loc="upper left")
    ax.grid(True)

if __name__ == "__main__":
    # Configure asyncio on Windows
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # Set up the plot
    fig, ax = plt.subplots()
    ani = FuncAnimation(fig, update_plot, interval=100)

    # Run BLE communication and plot together
    try:
        loop = asyncio.get_event_loop()
        # Run BLE in the event loop
        loop.create_task(connect_and_listen(DEVICE_ADDRESS))
        # Run the plot in the same thread
        plt.show()
    except KeyboardInterrupt:
        print("[INFO] Program interrupted.")
    finally:
        loop.run_until_complete(asyncio.sleep(0.1))  # Ensure graceful shutdown
        loop.close()
