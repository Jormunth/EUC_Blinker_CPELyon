import tkinter as tk
from tkinter import scrolledtext, ttk
import serial
import threading
import json
import csv
import os
from datetime import datetime

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

def send_data():
    data = entry.get()
    if data:
        ser.write(data.encode('utf-8'))  # Send data
        entry.delete(0, tk.END)  # Clear the input field

def read_data():
    while True:
        if ser.in_waiting > 0:
            received = ser.readline().decode('utf-8').strip()  # Read and decode
            # Efface la zone de texte avant d'afficher le nouveau message
            text_area.delete(1.0, tk.END)
            text_area.insert(tk.END, f"{received}\n")
            text_area.see(tk.END)  # Auto-scroll to the bottom

            #Mise à jour grille
            update_grid(received)

            # Archiver les données
            archive_data(received)

import csv

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

# Create the main Tkinter window
root = tk.Tk()
root.title("Serial Interface")

# Create the top frame for connection settings
settings_frame = tk.Frame(root)
settings_frame.pack(pady=10, fill=tk.X)

# Port selection
tk.Label(settings_frame, text="Port:").pack(side=tk.LEFT, padx=5)
port_combobox = ttk.Combobox(settings_frame, values=["/dev/ttyACM0", "/dev/ttyUSB0", "COM3"], width=15)
port_combobox.set("/dev/ttyACM0")
port_combobox.pack(side=tk.LEFT, padx=5)

# Baudrate selection
tk.Label(settings_frame, text="Baudrate:").pack(side=tk.LEFT, padx=5)
baudrate_combobox = ttk.Combobox(settings_frame, values=["9600", "19200", "38400", "115200", "460800"], width=10)
baudrate_combobox.set("460800")
baudrate_combobox.pack(side=tk.LEFT, padx=5)

# Connect button
connect_button = tk.Button(settings_frame, text="Connect", command=connect_serial)
connect_button.pack(side=tk.LEFT, padx=10)

# Disconnect button
disconnect_button = tk.Button(settings_frame, text="Disconnect", command=disconnect_serial, state=tk.DISABLED)
disconnect_button.pack(side=tk.LEFT, padx=10)

# Stop button
stop_button = tk.Button(settings_frame, text="Arrêt", command=root.destroy)  # Commande pour fermer la fenêtre
stop_button.pack(side=tk.LEFT, padx=10)

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

# Close the serial connection when the program exits
if 'ser' in globals() and ser:
    ser.close()
