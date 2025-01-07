import tkinter as tk
from tkinter import scrolledtext, ttk
import asyncio
from bleak import BleakClient
import json
import csv
import os
from datetime import datetime

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
SERVICE_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"  # Remplacez si nécessaire
CHARACTERISTIC_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"  # Remplacez si nécessaire

async def log_ble_data():
    DEVICE_ADDRESS = device_address_entry.get()  # Récupérer l'adresse du périphérique saisie
    async with BleakClient(DEVICE_ADDRESS) as client:
        print(f"Connexion au périphérique {DEVICE_ADDRESS}")

        # Vérifiez les services et caractéristiques du périphérique
        services = await client.get_services()
        print("Services et caractéristiques :")
        for service in services:
            print(f"Service UUID: {service.uuid}")
            for char in service.characteristics:
                print(f"\tCaractéristique UUID: {char.uuid}")
        
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

        # Fonction pour traiter les notifications BLE
        def handle_notification(sender, data):
            line = data.decode("utf-8").strip()
            print(f"Données reçues : {line}")
            try:
                data = line.split(",")
                if len(data) == 6:
                    timestamp = datetime.now().isoformat()  # Horodatage
                    archive_data(timestamp, data)
                    update_grid(data)
            except (IndexError, ValueError):
                print("Erreur de parsing :", line)

        # Ouvrir les notifications
        await client.start_notify(CHARACTERISTIC_UUID, handle_notification)
        print("Notifications activées. Appuyez sur Ctrl+C pour arrêter.")
        
        # Attente pour recevoir les notifications
        while True:
            await asyncio.sleep(1)

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
    Met à jour la grille 8x8 avec les valeurs extraites des données.
    :param data: Chaîne de caractères sous forme "-2:4,1:4,..."
    """

    try:
        # Transformer les données en une liste d'entiers
        values = [item.split(':')[0] for item in data.split(',') if ':' in item]
        # Remplir les cases de la grille (8x8)
        for i, label in enumerate(sum(grid_labels, [])):  # Transforme la grille en liste 1D
            if i < len(values):
                label.config(text=values[i])  # Mettre à jour le texte
                print("test1\n")
                # Couleur basée sur la valeur
                if values[i] == 'X':
                    label.config(bg="grey")
                else:
                    print("test2\n")
                    print(values[i])
                    label.config(bg=get_color(values[i]))
            else:
                label.config(text="", bg="white")  # Vider les cases restantes
    except Exception as e:
        print("Erreur lors de la mise à jour de la grille : {e}\n")

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
# Tkinter
##################################

# Create the main Tkinter window
root = tk.Tk()
root.title("TOF BLE GUI")

# Create the top frame for connection settings
settings_frame = tk.Frame(root)
settings_frame.pack(pady=10, fill=tk.X)

# Champ adresse du périphérique
device_address_label = tk.Label(settings_frame, text="Device Address:")
device_address_label.pack(side=tk.LEFT, padx=10)

device_address_entry = tk.Entry(settings_frame, width=20)
device_address_entry.pack(side=tk.LEFT, padx=10)

# Connect button
connect_button = tk.Button(settings_frame, text="Connect", command=lambda: asyncio.run(log_ble_data()))
connect_button.pack(side=tk.LEFT, padx=10)

# Stop button
stop_button = tk.Button(settings_frame, text="Arrêt", command=root.destroy)  # Commande pour fermer la fenêtre
stop_button.pack(side=tk.LEFT, padx=10)

# Create the resizable text area
text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD)
text_area.pack(pady=10, fill=tk.BOTH, expand=True)

# Cadre pour la grille 8x8
grid_frame = tk.Frame(root)
grid_frame.pack(pady=10)

# Création d'une grille de 8x8 cases
grid_labels = []
for row in range(8):
    row_labels = []
    for col in range(8):
        label = tk.Label(grid_frame, text="", width=4, height=2, borderwidth=1, relief="solid", font=("Arial", 10))
        label.grid(row=row, column=col, padx=2, pady=2)
        row_labels.append(label)
    grid_labels.append(row_labels)

# Run the Tkinter event loop
root.mainloop()

