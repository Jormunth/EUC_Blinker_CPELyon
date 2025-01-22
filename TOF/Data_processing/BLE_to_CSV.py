import asyncio
from bleak import BleakClient, BleakScanner
import csv
import os
from datetime import datetime

# Configuration des archives
archive_folder_csv = "Archives_csv"
if not os.path.exists(archive_folder_csv):
    os.makedirs(archive_folder_csv)
archive_filename_csv = os.path.join(archive_folder_csv, f"archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

# Configuration BLE
SERVICE_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
CHARACTERISTIC_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"

def save_to_csv(data):
    """
    Enregistre les données reçues dans un fichier CSV.
    :param data: Chaîne contenant les données à sauvegarder.
    """
    timestamp = datetime.now().isoformat()
    file_exists = os.path.isfile(archive_filename_csv)
    with open(archive_filename_csv, "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(["Timestamp", "Data"])  # En-têtes du fichier
        writer.writerow([timestamp] + data.split(','))

async def log_ble_data(device_address):
    """
    Se connecte à un périphérique BLE et enregistre les données reçues.
    :param device_address: Adresse MAC du périphérique BLE.
    """
    async with BleakClient(device_address) as client:
        print(f"Connexion au périphérique {device_address}")

        # Vérifiez les services et caractéristiques du périphérique
        services = await client.get_services()
        characteristic_found = any(
            char.uuid == CHARACTERISTIC_UUID
            for service in services
            for char in service.characteristics
        )

        if not characteristic_found:
            print("Caractéristique non trouvée.")
            return

        def handle_notification(sender, data):
            line = data.decode("utf-8").strip()
            print(f"Données reçues : {line}")
            save_to_csv(line)

        await client.start_notify(CHARACTERISTIC_UUID, handle_notification)
        print("Notifications activées. Appuyez sur Ctrl+C pour arrêter.")
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("Arrêt des notifications.")
        finally:
            await client.stop_notify(CHARACTERISTIC_UUID)

async def scan_devices():
    """
    Recherche et affiche les périphériques BLE disponibles.
    """
    print("Scan des périphériques BLE en cours...")
    devices = await BleakScanner.discover()
    if not devices:
        print("Aucun périphérique détecté.")
    else:
        print(f"{len(devices)} périphérique(s) détecté(s) :")
        for device in devices:
            if device.name!=None :
                print(f"Nom : {device.name}, Adresse MAC : {device.address}")

def main():
    print("Bienvenue dans l'application BLE.")
    print("Options :")
    print("1. Scanner les périphériques BLE")
    print("2. Se connecter à un périphérique BLE")
    choice = input("Choisissez une option : ")

    if choice == "1":
        asyncio.run(scan_devices())
    elif choice == "2":
        device_address = input("Entrez l'adresse MAC du périphérique : ")
        asyncio.run(log_ble_data(device_address))
    else:
        print("Option invalide.")

if __name__ == "__main__":
    main()
