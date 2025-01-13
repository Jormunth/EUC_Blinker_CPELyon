from datetime import datetime
import asyncio
from bleak import BleakClient

# Adresse MAC de votre ESP32 (à remplacer par l'adresse de votre périphérique)
DEVICE_ADDRESS = "F8:B3:B7:22:2E:3A"

# UUID du service et de la caractéristique BLE
SERVICE_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"  # Remplacez si nécessaire
CHARACTERISTIC_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"  # Remplacez si nécessaire

async def log_ble_data():
    async with BleakClient(DEVICE_ADDRESS) as client:
        # Vérifiez les services et caractéristiques du périphérique
        services = await client.get_services()
        
        # Vérifiez si la caractéristique souhaitée existe
        characteristic_found = False
        for service in services:
            for char in service.characteristics:
                if char.uuid == CHARACTERISTIC_UUID:
                    characteristic_found = True
                    break
        
        if not characteristic_found:
            print("Caractéristique non trouvée.")
            return

        print("# IKS01A3")
        print()
        print("time[us],acc_x[mg],acc_y[mg],acc_z[mg],gyro_x[mdps],gyro_y[mdps],gyro_z[mdps]")
 
        try:
            # Fonction pour traiter les notifications BLE
            def handle_notification(sender, data):
                line = data.decode("utf-8").strip()
                timestamp = datetime.now().isoformat()
                print(f"{timestamp},{line.replace('left,', '')}")

            # Activer les notifications sur la caractéristique
            await client.start_notify(CHARACTERISTIC_UUID, handle_notification)
            # print("Notifications activées. Appuyez sur Ctrl+C pour arrêter.")
            
            # Attente pour recevoir les notifications
            while True:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            pass
            # print("\nArrêt du logging.")
        finally:
            await client.stop_notify(CHARACTERISTIC_UUID)
            # print("Notifications désactivées.")

if __name__ == "__main__":
    asyncio.run(log_ble_data())
