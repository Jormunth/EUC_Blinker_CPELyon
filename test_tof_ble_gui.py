import tkinter as tk
from tkinter import scrolledtext, ttk
import asyncio
from bleak import BleakClient
import re
from bleak import BleakScanner
import json
import csv
import os
from datetime import datetime
import threading

##################################
#
# Archives
#
##################################
# Créer un dossier pour les archives si inexistant
archive_folder_json = "Archives_json"
if not os.path.exists(archive_folder_json):
    os.makedirs(archive_folder_json)

# Générer un nom de fichier unique pour cette exécution
archive_filename_json = os.path.join(archive_folder_json, f"archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

# Créer un dossier pour les archives si inexistant
archive_folder_csv = "Archives_csv"
if not os.path.exists(archive_folder_csv):
    os.makedirs(archive_folder_csv)

# Générer un nom de fichier unique pour cette exécution
archive_filename_csv = os.path.join(archive_folder_csv, f"archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

##################################
# BLE Configuration
##################################
SERVICE_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
CHARACTERISTIC_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"

# Variables globales
ble_task = None

async def log_ble_data():
    """
    Fonction pour se connecter au périphérique BLE et gérer les notifications.
    """
    DEVICE_ADDRESS = device_address_entry.get()
    async with BleakClient(DEVICE_ADDRESS) as client:
        print(f"Connexion au périphérique {DEVICE_ADDRESS}")
        services = await client.get_services()
        print("Services disponibles :")
        for service in services:
            print(f"Service UUID: {service.uuid}")
            for char in service.characteristics:
                print(f"\tCaractéristique UUID: {char.uuid}")
        
        if CHARACTERISTIC_UUID not in [char.uuid for char in services.characteristics]:
            print("Caractéristique non trouvée.")
            return

        def handle_notification(sender, data):
            line = data.decode("utf-8").strip()
            print(f"Données reçues : {line}")
            text_area.delete(1.0, tk.END)
            text_area.insert(tk.END, f"{line}\n")
            text_area.see(tk.END)
            try:
                archive_data(line)
                update_grid(line)
            except Exception as e:
                print(f"Erreur de traitement des données : {e}")

        await client.start_notify(CHARACTERISTIC_UUID, handle_notification)
        print("Notifications activées. Appuyez sur Ctrl+C pour arrêter.")
        while True:
            await asyncio.sleep(1)

async def scan_ble_devices():
    scan_text_area.delete(1.0, tk.END)
    scan_text_area.insert(tk.END, "Scan des périphériques BLE en cours...\n")
    devices = await BleakScanner.discover()
    if not devices:
        scan_text_area.insert(tk.END, "Aucun périphérique détecté.\n")
    else:
        scan_text_area.insert(tk.END, f"{len(devices)} périphérique(s) détecté(s) :\n")
        for device in devices:
            scan_text_area.insert(tk.END, f"Nom : {device.name}, Adresse MAC : {device.address}\n")


##################################
# Intégration asyncio et Tkinter
##################################
def run_coroutine_threadsafe(coroutine):
    """
    Démarre une coroutine asyncio dans la boucle d'événements en arrière-plan.
    """
    asyncio.run_coroutine_threadsafe(coroutine, asyncio.get_event_loop())

def asyncio_thread():
    """
    Démarre la boucle asyncio dans un thread séparé.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_forever()

##################################
# Archivage // Grid
##################################

def archive_data(data):
    """
    Archive les données reçues dans un fichier JSON et un fichier CSV avec un horodatage.
    :param data: Les données reçues sous forme de chaîne.
    """
    timestamp = datetime.now().isoformat()  # Format de l'horodatage
    archive_entry = {"timestamp": timestamp, "data": data}  # Structure des données

    # Sauvegarde JSON
    try:
        with open(archive_filename_json, "r") as file:
            archive = json.load(file)  # Charger les données existantes
    except (FileNotFoundError, json.JSONDecodeError):
        archive = []  # Initialiser une nouvelle liste pour cette exécution

    # Ajouter la nouvelle entrée
    archive.append(archive_entry)

    # Écrire les données mises à jour dans le fichier JSON
    with open(archive_filename_json, "w") as file:
        json.dump(archive, file, indent=4)  # Sauvegarde avec indentation pour lisibilité

    # Sauvegarde CSV
    file_exists = os.path.isfile(archive_filename_csv)  # Vérifie si le fichier CSV existe déjà
    with open(archive_filename_csv, "a", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)
        if not file_exists:
            csv_writer.writerow(["Timestamp", "Data"])  # Écrire l'en-tête uniquement si le fichier est nouveau
        csv_writer.writerow([timestamp]+ data.split(','))  # Ajouter une ligne de données


def update_grid(data):
    """
    Met à jour la grille 8x8 avec les valeurs extraites des données, en commençant
    par le coin inférieur gauche, de gauche à droite, puis de bas en haut.
    :param data: Chaîne de caractères sous forme "-2:4,1:4,..."
    """
    try:
        # Transformer les données en une liste d'entiers
        values = [item.split(':')[0] for item in data.split(',') if ':' in item]

        # Parcourir les cases en partant du bas
        index = 0
        for row in range(7, -1, -1):  # Parcourt les lignes de bas en haut
            for col in range(8):  # Parcourt les colonnes de gauche à droite
                if index < len(values):
                    value = values[index]
                    label = grid_labels[row][col]
                    label.config(text=value)  # Mettre à jour le texte
                    # Couleur basée sur la valeur
                    if value == 'X':
                        label.config(bg="grey")
                    else:
                        label.config(bg=get_color(value))
                    index += 1
                else:
                    # Si plus de données, vider la case
                    label = grid_labels[row][col]
                    label.config(text="", bg="white")

    except Exception as e:
        print(f"Erreur lors de la mise à jour de la grille : {e}\n")

def get_color(value):
    """
    Génère une couleur RGB correspondant à un gradient allant de rouge (0) à vert (4000).
    :param value: La valeur entre 0 et 4000.
    :return: Une couleur hexadécimale (#RRGGBB).
    """
    try:
        # Normalisation de la valeur entre 0 et 1
        normalized = max(0, min(int(value) / 4000, 1))
        # Calcul des composantes rouge et verte pour le gradient
        red = int((1 - normalized) * 255)  # Diminue le rouge
        green = int(normalized * 255)  # Augmente le vert
        # Retourne une couleur hexadécimale (#RRGGBB)
        return f"#{red:02x}{green:02x}00"
    except Exception as e:
        print(f"Erreur dans get_color: {e}")
        return "#ffffff"  # Retourne blanc en cas d'erreur


##################################
# Tkinter GUI
##################################
root = tk.Tk()
root.title("TOF BLE GUI")

settings_frame = tk.Frame(root)
settings_frame.pack(pady=10, fill=tk.X)

device_address_label = tk.Label(settings_frame, text="Device Address:")
device_address_label.pack(side=tk.LEFT, padx=10)

device_address_entry = tk.Entry(settings_frame, width=20)
device_address_entry.pack(side=tk.LEFT, padx=10)

connect_button = tk.Button(settings_frame, text="Connect", command=lambda: run_coroutine_threadsafe(log_ble_data()))
connect_button.pack(side=tk.LEFT, padx=10)

scan_button = tk.Button(settings_frame, text="Scan", command=lambda: run_coroutine_threadsafe(scan_ble_devices()))
scan_button.pack(side=tk.LEFT, padx=10)

stop_button = tk.Button(settings_frame, text="Arrêt", command=root.destroy)
stop_button.pack(side=tk.LEFT, padx=10)

scan_text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=4)
scan_text_area.pack(pady=10, fill=tk.BOTH, expand=True)

text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=7)
text_area.pack(pady=10, fill=tk.BOTH, expand=True)

grid_frame = tk.Frame(root)
grid_frame.pack(pady=10)

grid_labels = []
for row in range(8):
    row_labels = []
    for col in range(8):
        label = tk.Label(grid_frame, text="", width=4, height=2, borderwidth=1, relief="solid", font=("Arial", 10))
        label.grid(row=row, column=col, padx=2, pady=2)
        row_labels.append(label)
    grid_labels.append(row_labels)

# Démarrer la boucle asyncio dans un thread séparé
thread = threading.Thread(target=asyncio_thread, daemon=True)
thread.start()

root.mainloop()