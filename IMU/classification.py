import sys
import asyncio
from collections import deque
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QMessageBox,
)
from bleak import BleakClient
from qasync import QEventLoop
import numpy as np

class Classification:
    def __init__(self):
        self.WINDOW_LENGTH = 52

        self.time_buffer = deque(maxlen=self.WINDOW_LENGTH)
        self.acc_x_buffer = deque(maxlen=self.WINDOW_LENGTH)
        self.acc_y_buffer = deque(maxlen=self.WINDOW_LENGTH)
        self.acc_z_buffer = deque(maxlen=self.WINDOW_LENGTH)
        self.gyro_x_buffer = deque(maxlen=self.WINDOW_LENGTH)
        self.gyro_y_buffer = deque(maxlen=self.WINDOW_LENGTH)
        self.gyro_z_buffer = deque(maxlen=self.WINDOW_LENGTH)

    def add_data(self, data_string):
        try:
            values = data_string.split(',')
            if len(values) == 7:  # Ensure correct data format
                self.time_buffer.append(float(values[0]))
                self.acc_x_buffer.append(float(values[1]))
                self.acc_y_buffer.append(float(values[2]))
                self.acc_z_buffer.append(float(values[3]))
                self.gyro_x_buffer.append(float(values[4]))
                self.gyro_y_buffer.append(float(values[5]))
                self.gyro_z_buffer.append(float(values[6]))
                return self.classify()
        except ValueError:
            print(f"[ERREUR] Impossible de convertir les données : {data_string}")
        except Exception as e:
            print(f"[ERREUR] Erreur inattendue lors de l'ajout des données : {e}")

    def calculate_norm(self, buffer_x, buffer_y, buffer_z):
        """
        Calculate the norm for a deque buffer containing X, Y, and Z components.

        Args:
            buffer_x (deque): Deque containing X-component data.
            buffer_y (deque): Deque containing Y-component data.
            buffer_z (deque): Deque containing Z-component data.

        Returns:
            list: A list of norms corresponding to each index in the buffer.
        """
        # Ensure all buffers have the same length
        if not (len(buffer_x) == len(buffer_y) == len(buffer_z)):
            raise ValueError("All buffers must have the same length.")

        # Compute norms
        norms = [
            np.sqrt(x**2 + y**2 + z**2)
            for x, y, z in zip(buffer_x, buffer_y, buffer_z)
        ]

        return norms


    def classify(self):
        # Extract features based on the decision tree
        acc_norm_list = self.calculate_norm(self.acc_x_buffer, self.acc_y_buffer, self.acc_z_buffer)
        gyro_norm_list = self.calculate_norm(self.gyro_x_buffer, self.gyro_y_buffer, self.gyro_z_buffer)
        f3_mean_acc_v = np.mean(acc_norm_list) if self.acc_x_buffer else 0
        f4_mean_gyr_v = np.mean(gyro_norm_list) if self.gyro_x_buffer else 0
        f2_abs_peak_detector_gyr_v = max(self.gyro_x_buffer + self.gyro_y_buffer + self.gyro_z_buffer) - min(self.gyro_x_buffer + self.gyro_y_buffer + self.gyro_z_buffer) if self.gyro_x_buffer else 0

        # Apply the decision tree logic
        if f3_mean_acc_v <= 1.0558:
            if f3_mean_acc_v <= 1.0459:
                if f4_mean_gyr_v <= 1.62695:
                    return "other"
                else:
                    return "d_shake"
            else:
                return "stationnary"
        else:
            if f2_abs_peak_detector_gyr_v <= 13:
                return "chest_tap"
            else:
                return "d_shake"

class BLEClientWorker(QThread):
    connection_success = pyqtSignal(str)
    connection_error = pyqtSignal(str)
    notification_received = pyqtSignal(str)

    def __init__(self, address, BLEApp):
        super().__init__()
        self.address = address
        self.BLEApp = BLEApp

    def run(self):
        asyncio.run(self.connect_and_listen())

    async def connect_and_listen(self):
        try:
            print(f"[CONNEXION] Connexion au périphérique BLE à l'adresse {self.address}...")
            self.BLEApp.client = BleakClient(self.address)
            await self.BLEApp.client.connect()
            if self.BLEApp.client.is_connected:
                self.connection_success.emit(self.address)

                # Enable notifications
                def handle_notification(sender, data):
                    self.notification_received.emit(data.decode('utf-8', errors='ignore'))

                char_uuid = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
                await self.BLEApp.client.start_notify(char_uuid, handle_notification)

                # Continuously listen for notifications
                while self.BLEApp.client.is_connected:
                    await asyncio.sleep(1)

        except Exception as e:
            self.connection_error.emit(str(e))

class BLEApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BLE Device Manager")
        self.setGeometry(100, 100, 400, 400)

        self.client = None
        self.ble_address = "F8:B3:B7:22:2E:3A"  # Hardcoded BLE address
        self.classification = Classification()
        self.classification_enabled = False  # Flag to control classification

        # UI Elements
        layout = QVBoxLayout()

        self.connect_button = QPushButton("Connecter")
        self.connect_button.clicked.connect(self.connect_device)
        layout.addWidget(self.connect_button)

        self.disconnect_button = QPushButton("Se déconnecter")
        self.disconnect_button.clicked.connect(self.disconnect_device)
        self.disconnect_button.setEnabled(False)
        layout.addWidget(self.disconnect_button)

        self.toggle_classification_button = QPushButton("Activer la classification")
        self.toggle_classification_button.clicked.connect(self.toggle_classification)
        layout.addWidget(self.toggle_classification_button)

        self.status_label = QLabel("Statut : En attente")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        self.data_label = QLabel("Données BLE :")
        layout.addWidget(self.data_label)

        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        layout.addWidget(self.text_area)

        self.classification_label = QLabel("Classification : En attente")
        layout.addWidget(self.classification_label)

        self.setLayout(layout)

    def toggle_classification(self):
        """
        Toggle the classification functionality on or off.
        """
        self.classification_enabled = not self.classification_enabled
        if self.classification_enabled:
            self.toggle_classification_button.setText("Désactiver la classification")
            self.classification_label.setText("Classification : Activée")
        else:
            self.toggle_classification_button.setText("Activer la classification")
            self.classification_label.setText("Classification : Désactivée")

    def connect_device(self):
        print(f"[CONNEXION] Tentative de connexion au périphérique à l'adresse : {self.ble_address}")
        self.status_label.setText(f"Statut : Connexion à {self.ble_address}...")
        self.client_worker = BLEClientWorker(self.ble_address, self)
        self.client_worker.connection_success.connect(self.on_connection_success)
        self.client_worker.connection_error.connect(self.on_connection_error)
        self.client_worker.notification_received.connect(self.on_notification_received)
        self.client_worker.start()

    def on_connection_success(self, address):
        print(f"[CONNEXION] Connecté avec succès à {address}.")
        self.status_label.setText(f"Statut : Connecté à {address}")
        self.connect_button.setEnabled(False)
        self.disconnect_button.setEnabled(True)

    def on_connection_error(self, error):
        print(f"[CONNEXION] Erreur lors de la connexion : {error}")
        self.status_label.setText(f"Erreur : {error}")
        QMessageBox.critical(self, "Erreur", f"Une erreur s'est produite : {error}")

    def on_notification_received(self, data):
        print(f"[NOTIFICATION] {data}")
        self.text_area.append(data)
        if self.classification_enabled:  # Process data only if classification is enabled
            classification_result = self.classification.add_data(data)
            if classification_result:
                self.classification_label.setText(f"Classification : {classification_result}")

    def disconnect_device(self):
        if self.client and self.client.is_connected:
            print("[DÉCONNEXION] Déconnexion en cours...")
            asyncio.ensure_future(self.async_disconnect_device())

    async def async_disconnect_device(self):
        try:
            await self.client.disconnect()
            print("[DÉCONNEXION] Déconnecté avec succès.")
            self.on_disconnect_success()
        except Exception as e:
            print(f"[DÉCONNEXION] Erreur lors de la déconnexion : {e}")
            self.on_disconnect_error(str(e))

    def on_disconnect_success(self):
        self.status_label.setText("Statut : Déconnecté.")
        self.connect_button.setEnabled(True)
        self.disconnect_button.setEnabled(False)
        self.client = None

    def on_disconnect_error(self, error):
        self.status_label.setText(f"Erreur : {error}")
        QMessageBox.critical(self, "Erreur", f"Une erreur s'est produite : {error}")

if __name__ == "__main__":
    app = QApplication([])

    # Boucle événementielle asynchrone
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = BLEApp()
    window.show()

    with loop:
        loop.run_forever()
