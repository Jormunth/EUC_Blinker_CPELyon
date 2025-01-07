import sys
import serial
import numpy as np
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtDataVisualization import (
    Q3DSurface, QSurfaceDataProxy, QSurface3DSeries,
    QAbstract3DGraph, QValue3DAxis)
from PySide6.QtGui import QVector3D

class Serial3DPlot(QMainWindow):
    def __init__(self, serial_port, baud_rate, parent=None):
        super().__init__(parent)

        # Initialize serial connection
        self.serial = serial.Serial(serial_port, baud_rate, timeout=1)

        # Set up the 3D surface graph
        self.graph = Q3DSurface()
        self.proxy = QSurfaceDataProxy()
        self.series = QSurface3DSeries(self.proxy)

        self.graph.addSeries(self.series)

        # Configure the axes
        self.graph.axisX().setTitle("X Axis")
        self.graph.axisY().setTitle("Y Axis")
        self.graph.axisZ().setTitle("Z Axis")
        self.graph.axisX().setTitleVisible(True)
        self.graph.axisY().setTitleVisible(True)
        self.graph.axisZ().setTitleVisible(True)

        self.setCentralWidget(self.graph)

        # Start updating the graph
        self.timer_id = self.startTimer(100)

    def timerEvent(self, event):
        if self.serial.in_waiting > 0:
            try:
                line = self.serial.readline().decode('utf-8').strip()
                data = np.array([float(v) for v in line.split(',')]).reshape((10, 10))

                # Populate the proxy with the new data
                rows, cols = data.shape
                array = QSurfaceDataProxy.Array()

                for i in range(rows):
                    row = QSurfaceDataProxy.Row()
                    for j in range(cols):
                        row.append(QVector3D(j, data[i, j], i))
                    array.append(row)

                self.proxy.resetArray(array)

            except Exception as e:
                print(f"Error reading serial data: {e}")

    def closeEvent(self, event):
        self.killTimer(self.timer_id)
        self.serial.close()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Update these with the correct serial port and baud rate
    serial_port = "/dev/ttyACM0"  # or "/dev/ttyUSB0" on Linux
    baud_rate = 460800

    window = Serial3DPlot(serial_port, baud_rate)
    window.setWindowTitle("3D Serial Data Plot")
    window.resize(800, 600)
    window.show()

    sys.exit(app.exec())
