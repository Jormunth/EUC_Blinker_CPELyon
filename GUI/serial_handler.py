import serial
import threading

class SerialHandler:
    def __init__(self, text_area):
        self.ser = None
        self.text_area = text_area

    def connect(self, port, baudrate):
        try:
            self.ser = serial.Serial(port, baudrate, timeout=1)
            threading.Thread(target=self.read_data, daemon=True).start()
            return True
        except serial.SerialException as e:
            self.text_area.insert('end', f"Error: {e}\n")
            return False

    def read_data(self):
        while self.ser and self.ser.is_open:
            if self.ser.in_waiting > 0:
                received = self.ser.readline().decode('utf-8').strip()
                self.text_area.insert('end', f"{received}\n")
                self.text_area.see('end')

    def disconnect(self):
        if self.ser:
            self.ser.close()
            self.ser = None
