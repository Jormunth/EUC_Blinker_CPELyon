import sys
import os
import asyncio
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QTextEdit,
    QMessageBox,
    QSpinBox,
)
from bleak import BleakScanner, BleakClient
from qasync import QEventLoop
import csv
from datetime import datetime

class BLEClientWorker(QThread):
    connection_success = pyqtSignal(str)
    connection_error = pyqtSignal(str)
    notification_received = pyqtSignal(bytearray)

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
                    self.notification_received.emit(data)

                char_uuid = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
                await self.BLEApp.client.start_notify(char_uuid, handle_notification)

                # Continuously listen for notifications
                while self.BLEApp.client.is_connected:
                    await asyncio.sleep(1)  # Check if still connected every second

                print(f"[CONNEXION] Notifications désactivées pour {self.address}.")

        except Exception as e:
            self.connection_error.emit(str(e))


class BLEWorker(QThread):
    devices_found = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def run(self):
        asyncio.run(self.scan_devices())

    async def scan_devices(self):
        print("[SCAN] Début du scan BLE...")
        try:
            devices = await BleakScanner.discover()
            result = {device.name: device.address for device in devices if device.name}
            print(f"[SCAN] Périphériques trouvés : {result}")
            self.devices_found.emit(result)
        except Exception as e:
            print(f"[SCAN] Erreur lors du scan : {e}")
            self.error_occurred.emit(str(e))

class BLEApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BLE Device Manager")
        self.setGeometry(100, 100, 500, 500)

        self.devices = {}
        self.selected_device = None
        self.client = None
        self.is_logging = False
        self.log_timer = None

        # UI Elements
        layout = QVBoxLayout()

        self.device_label = QLabel("Périphériques BLE détectés :")
        layout.addWidget(self.device_label)

        self.device_dropdown = QComboBox()
        self.device_dropdown.setEditable(False)
        layout.addWidget(self.device_dropdown)

        self.scan_button = QPushButton("Scanner")
        self.scan_button.clicked.connect(self.scan_devices)
        layout.addWidget(self.scan_button)

        self.connect_button = QPushButton("Connecter")
        self.connect_button.clicked.connect(self.connect_device)
        layout.addWidget(self.connect_button)

        self.disconnect_button = QPushButton("Se déconnecter")
        self.disconnect_button.clicked.connect(self.disconnect_device)
        self.disconnect_button.setEnabled(False)
        layout.addWidget(self.disconnect_button)

        self.timeout_label = QLabel("Durée de l'enregistrement (secondes) :")
        layout.addWidget(self.timeout_label)

        self.timeout_selector = QSpinBox()
        self.timeout_selector.setMinimum(1)
        self.timeout_selector.setMaximum(3600)
        self.timeout_selector.setValue(10)  # Default to 10 seconds
        layout.addWidget(self.timeout_selector)

        self.log_button = QPushButton("Démarrer l'enregistrement")
        self.log_button.clicked.connect(self.start_logging)
        layout.addWidget(self.log_button)

        self.close_button = QPushButton("Fermer l'application")
        self.close_button.clicked.connect(self.close_application)
        layout.addWidget(self.close_button)

        self.status_label = QLabel("Statut : En attente")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        self.data_label = QLabel("Données BLE :")
        layout.addWidget(self.data_label)

        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        layout.addWidget(self.text_area)

        self.setLayout(layout)

    def scan_devices(self):
        print("[SCAN] Bouton 'Scanner' cliqué.")
        self.status_label.setText("Statut : Scan en cours...")
        self.worker = BLEWorker()
        self.worker.devices_found.connect(self.update_devices)
        self.worker.error_occurred.connect(self.show_error)
        self.worker.start()

    def update_devices(self, devices):
        print(f"[SCAN] Mise à jour des périphériques : {devices}")
        self.devices = devices
        self.device_dropdown.clear()
        self.device_dropdown.addItems(self.devices.keys())
        if self.devices:
            self.status_label.setText(f"Statut : {len(self.devices)} périphérique(s) trouvé(s).")
        else:
            self.status_label.setText("Statut : Aucun périphérique trouvé.")

    def show_error(self, error):
        print(f"[ERREUR] {error}")
        self.status_label.setText(f"Erreur : {error}")
        QMessageBox.critical(self, "Erreur", f"Une erreur s'est produite : {error}")

    def connect_device(self):
        device_name = self.device_dropdown.currentText()
        print(f"[CONNEXION] Tentative de connexion au périphérique : {device_name}")
        if not device_name:
            QMessageBox.warning(self, "Avertissement", "Veuillez sélectionner un périphérique.")
            return

        address = self.devices.get(device_name)
        if not address:
            print("[CONNEXION] Adresse introuvable.")
            QMessageBox.warning(self, "Avertissement", "Adresse introuvable pour le périphérique sélectionné.")
            return

        self.status_label.setText(f"Statut : Connexion à {address}...")
        self.client_worker = BLEClientWorker(address, self)
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
        data = data.decode('utf-8', errors='ignore')
        print(f"[NOTIFICATION] {data}")
        self.text_area.append(data)
        if self.is_logging:
            self.save_log(data)

    def disconnect_device(self):
        if self.client and self.client.is_connected:
            print("[DÉCONNEXION] Déconnexion en cours...")
            # Demander une déconnexion asynchrone dans la boucle événementielle
            asyncio.ensure_future(self.async_disconnect_device())

    async def async_disconnect_device(self):
        try:
            await self.client.disconnect()
            print("[DÉCONNEXION] Déconnecté avec succès.")
            
            # Mettez à jour l'interface graphique dans le thread principal en utilisant QMetaObject
            QMetaObject.invokeMethod(self, "on_disconnect_success", Qt.QueuedConnection)

        except Exception as e:
            print(f"[DÉCONNEXION] Erreur lors de la déconnexion : {e}")
            # Mettez à jour l'interface graphique avec une erreur
            QMetaObject.invokeMethod(self, "on_disconnect_error", Qt.QueuedConnection, Q_ARG(str, str(e)))

    def on_disconnect_success(self):
        self.status_label.setText("Statut : Déconnecté.")
        self.connect_button.setEnabled(True)
        self.disconnect_button.setEnabled(False)
        self.client = None

    def on_disconnect_error(self, error):
        self.status_label.setText(f"Erreur : {error}")
        QMessageBox.critical(self, "Erreur", f"Une erreur s'est produite : {error}")

    def close_application(self):
        print("[FERMETURE] Fermeture de l'application...")
        if self.client and self.client.is_connected:
            asyncio.run(self.async_disconnect_device())
        self.close()

    def start_logging(self):
        if not self.client or not self.client.is_connected:
            QMessageBox.warning(self, "Avertissement", "Veuillez d'abord vous connecter à un périphérique.")
            return

        self.is_logging = True
        self.log_button.setText("Arrêter l'enregistrement")

        # Get timeout from selector
        timeout = self.timeout_selector.value()
        self.status_label.setText(f"Enregistrement des données pendant {timeout} secondes...")
        
        # Set up a timer to stop logging after the timeout
        self.log_timer = QTimer(self)
        self.log_timer.timeout.connect(self.stop_logging)
        self.log_timer.start(timeout * 1000)  # Timeout in milliseconds

        # Create a log file
        self.log_file = self.create_log_file()

    def stop_logging(self):
        self.is_logging = False
        self.log_file.close()
        self.log_timer.stop()
        self.status_label.setText("Statut : Enregistrement terminé.")
        self.log_button.setText("Démarrer l'enregistrement")

    def create_log_file(self):
        # Create the filename based on current datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        logs_path = os.path.join("c:\\","Users","alixd","Documents","CPE","5A","projet_majeure","S6_G6_Deleule_Delzenne-Zamparutti","IMU","logs")
        filename = os.path.join(logs_path,f"{timestamp}_imu_logs.csv")
        print("Creating log file : " + filename)
        
        # Create the log directory if it doesn't exist
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        # Open the file for writing
        log_file = open(filename, mode="w", newline="")
        csv_writer = csv.writer(log_file)
        
        print("Filling the log file with the header rows.")
        csv_writer.writerow(["# IKS01A3 "])  # Header row
        csv_writer.writerow([" "])  # Header row
        csv_writer.writerow("time[us],acc_x[mg],acc_y[mg],acc_z[mg],gyro_x[mdps],gyro_y[mdps],gyro_z[mdps]".split(","))  # Header row
        return log_file

    def save_log(self, data):
        if self.is_logging and self.log_file:
            print("Writing log")
            csv_writer = csv.writer(self.log_file)
            csv_writer.writerow(data.split(","))

if __name__ == "__main__":
    app = QApplication([])

    # Boucle événementielle asynchrone
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = BLEApp()
    window.show()

    with loop:
        loop.run_forever()
