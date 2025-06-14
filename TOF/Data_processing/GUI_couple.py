import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import csv
import cv2
import os
import subprocess
from datetime import datetime, timedelta, timezone
import ffmpeg
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata
from PIL import Image, ImageTk

labeled_data = {}  # Dictionnaire pour stocker les données labélisées

def load_csv():
    filepath = filedialog.askopenfilename(
        title="Sélectionner un fichier CSV",
        filetypes=[("CSV files", "*.csv")]
    )
    if not filepath:
        file_label.config(text="Aucun fichier choisi")
        return
    try:
        with open(filepath, "r") as file:
            reader = csv.reader(file)
            global data, new_csv_path, labeled_data
            data = list(reader)
            timestamps = [row[0] for row in data if row]  # Collecte les timestamps
            timestamp_dropdown['values'] = timestamps
            file_label.config(text=f"Fichier choisi : {filepath.split('/')[-1]}")

            # Créer le dossier `data_label` s'il n'existe pas
            os.makedirs("data_label", exist_ok=True)

            # Chemin pour le nouveau fichier CSV
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            new_csv_path = os.path.join("data_label", f"labeled_data_{timestamp}.csv")
            
            # Charger les données existantes dans le dictionnaire
            if os.path.exists(new_csv_path):
                with open(new_csv_path, "r") as labeled_file:
                    labeled_reader = csv.reader(labeled_file)
                    next(labeled_reader, None)  # Sauter l'en-tête
                    labeled_data = {row[0]: row[1] for row in labeled_reader}

            # Créer le fichier si ce n'est pas encore fait
            else:
                with open(new_csv_path, "w", newline="") as new_file:
                    writer = csv.writer(new_file)
                    writer.writerow(["Data", "Label"])  # Entêtes

            print("Succès", "Fichier CSV chargé avec succès.")
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de charger le fichier : {e}")

def load_mp4():
    filepath = filedialog.askopenfilename(
        title="Sélectionner un fichier MP4",
        filetypes=[("MP4 files", "*.mp4")]
    )
    if not filepath:
        mp4_file_label.config(text="Aucun fichier MP4 choisi")
        return
    mp4_file_label.config(text=f"Fichier MP4 choisi : {filepath.split('/')[-1]}")
    print("Succès", "Fichier MP4 chargé avec succès.")


def on_timestamp_select(event):
    selected_timestamp = timestamp_var.get()
    if not selected_timestamp:
        return
    for row in data:
        if row[0] == selected_timestamp:
            text_area.delete("1.0", tk.END)
            text_area.insert(tk.END, ", ".join(row[1:66]))
            update_grid(", ".join(row[1:66]))

            # Charger et afficher l'image du fichier MP4
            if mp4_file_label.cget("text") != "Aucun fichier MP4 choisi":
                mp4_filename = mp4_file_label.cget("text").replace("Fichier MP4 choisi : ", "")
                mp4_filepath = os.path.join("vid",mp4_filename)
                frame = extract_frame_from_mp4(mp4_filepath, selected_timestamp)
                if frame is not None:
                    show_image_in_tkinter(frame)
            return


def update_grid(data):
    try:
        values = [item.split(':')[0] for item in data.split(',') if ':' in item]
        index = 0
        for row in range(7, -1, -1):
            for col in range(8):
                if index < len(values):
                    value = values[index]
                    label = grid_labels[row][col]
                    label.config(text=value)
                    if value == 'X':
                        label.config(bg="grey")
                    else:
                        label.config(bg=get_color(value))
                    index += 1
                else:
                    label = grid_labels[row][col]
                    label.config(text="", bg="white")
    except Exception as e:
        print(f"Erreur lors de la mise à jour de la grille : {e}\n")

def get_color(value):
    try:
        normalized = max(0, min(int(value) / 4000, 1))
        red = int((1 - normalized) * 255)
        green = int(normalized * 255)
        return f"#{red:02x}{green:02x}00"
    except Exception as e:
        print(f"Erreur dans get_color: {e}")
        return "#ffffff"

def stop_app():
    root.quit()

def normalize_timestamp(timestamp):
    if timestamp is None:
        raise ValueError("Le timestamp est vide. Vérifiez les données en entrée.")
    if timestamp.tzinfo is not None:
        return timestamp.astimezone(timezone.utc)
    return timestamp.replace(tzinfo=timezone.utc)

def get_video_timestamp(mp4_filepath):
    """
    Récupère le timestamp exact où la vidéo a été enregistrée à partir des métadonnées.
    Utilise la bibliothèque hachoir.
    """
    try:
        parser = createParser(mp4_filepath)
        if not parser:
            raise ValueError("Impossible de créer un parser pour le fichier MP4.")

        metadata = extractMetadata(parser)
        if not metadata:
            raise ValueError("Impossible d'extraire les métadonnées.")

        creation_time = metadata.get("creation_date")
        if not creation_time:
            raise ValueError("Timestamp de création non trouvé dans les métadonnées.")

        # Retourne le timestamp comme un objet datetime
        return creation_time

    except Exception as e:
        print(f"Erreur lors de l'extraction du timestamp : {e}")
        return None


def extract_frame_from_mp4(mp4_filepath, timestamp_str):
    """
    Extrait une frame d'un fichier MP4 à un timestamp donné en prenant en compte le timestamp
    de création de la vidéo et le timestamp du CSV.
    """
    # Récupérer la date de création du fichier vidéo
    video_creation_time = get_video_timestamp(mp4_filepath)
    print("video_norm")
    print(normalize_timestamp(video_creation_time))
    # Convertir le timestamp du CSV en datetime
    timestamp = datetime.fromisoformat(timestamp_str)
    print("csv_norm")
    print(normalize_timestamp(timestamp))
    # Calculer la différence entre le timestamp du CSV et la date de création de la vidéo
    time_diff = normalize_timestamp(timestamp) - normalize_timestamp(video_creation_time)
    print(time_diff)

    # Convertir cette différence en secondes
    timestamp_seconds = time_diff.total_seconds()

    # Ouvrir le fichier MP4
    cap = cv2.VideoCapture(mp4_filepath)
    if not cap.isOpened():
        print("Erreur d'ouverture du fichier MP4")
        return None

    # Calculer le numéro du frame en fonction du timestamp
    fps = cap.get(cv2.CAP_PROP_FPS)  # Nombre d'images par seconde
    frame_number = int(fps * timestamp_seconds)
    print("test3")
    print(frame_number)

    # Vérifier si le numéro de la frame est dans les limites de la vidéo
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if frame_number < 0:
        frame_number = 0  # Ne pas aller avant le début de la vidéo
    elif frame_number >= total_frames:
        frame_number = total_frames - 1  # Ne pas dépasser la dernière frame

    # Lire la frame à l'index calculé
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    ret, frame = cap.read()

    cap.release()
    if ret:
        return frame
    else:
        print(f"Impossible d'extraire la frame à {timestamp_str}")
        return None

def show_image_in_tkinter(frame):
    """ Affiche une frame OpenCV dans Tkinter """
    # Convertir la frame OpenCV (BGR) en RGB
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # Convertir l'image en objet PIL
    pil_image = Image.fromarray(frame_rgb)
    pil_image = pil_image.resize((300, 300))  # Redimensionner si nécessaire

    # Convertir en format compatible Tkinter
    tk_image = ImageTk.PhotoImage(pil_image)

    # Afficher l'image dans un label Tkinter
    image_label.config(image=tk_image)
    image_label.image = tk_image  # Garder une référence à l'image

def select_previous_timestamp():
    """Passe au timestamp précédent dans la liste."""
    current_timestamp = timestamp_var.get()
    if not current_timestamp or not data:
        return
    timestamps = [row[0] for row in data if row]
    if current_timestamp in timestamps:
        current_index = timestamps.index(current_timestamp)
        if current_index > 0:
            new_timestamp = timestamps[current_index - 1]
            timestamp_var.set(new_timestamp)
            on_timestamp_select(None)

def select_next_timestamp():
    """Passe au timestamp suivant dans la liste."""
    current_timestamp = timestamp_var.get()
    if not current_timestamp or not data:
        return
    timestamps = [row[0] for row in data if row]
    if current_timestamp in timestamps:
        current_index = timestamps.index(current_timestamp)
        if current_index < len(timestamps) - 1:
            new_timestamp = timestamps[current_index + 1]
            timestamp_var.set(new_timestamp)
            on_timestamp_select(None)

def save_label(label):
    """
    Sauvegarde ou met à jour les données actuelles de `text_area` avec le label donné dans le fichier CSV.
    """
    global new_csv_path, labeled_data
    try:
        data_to_save = text_area.get("1.0", tk.END).strip()  # Récupère le texte de la zone de texte
        if not data_to_save:
            messagebox.showwarning("Attention", "Aucune donnée à sauvegarder.")
            return
        
        select_next_timestamp()

        # Vérifier si les données existent déjà
        if data_to_save in labeled_data:
            labeled_data[data_to_save] = label  # Mettre à jour le label
            print("Mise à jour", f"Le label a été mis à jour pour '{data_to_save}'.")
        else:
            labeled_data[data_to_save] = label  # Ajouter une nouvelle entrée
            print("Succès", f"Données enregistrées avec le label '{label}'.")

        # Écrire les données dans le fichier CSV
        with open(new_csv_path, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Data", "Label"])  # Réécrire l'en-tête
            for data, lbl in labeled_data.items():
                writer.writerow([data, lbl])
            

    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de sauvegarder les données : {e}")


root = tk.Tk()
root.title("Affichage des données CSV")

data = []
timestamp_var = tk.StringVar()

frame = ttk.Frame(root, padding=10)
frame.grid(row=0, column=0, sticky="NSEW")

btn_load_csv = ttk.Button(frame, text="Charger un fichier CSV", command=load_csv)
btn_load_csv.grid(row=0, column=0, padx=5, pady=5, sticky="EW")

btn_load_mp4 = ttk.Button(frame, text="Charger un fichier MP4", command=load_mp4)
btn_load_mp4.grid(row=0, column=1, padx=5, pady=5, sticky="EW")

btn_stop = ttk.Button(frame, text="Arrêt", command=stop_app)
btn_stop.grid(row=0, column=2, padx=5, pady=5, sticky="EW")

ttk.Label(frame, text="Sélectionner un timestamp :").grid(row=2, column=0, padx=5, pady=5, sticky="W")
timestamp_dropdown = ttk.Combobox(frame, textvariable=timestamp_var, state="readonly")
timestamp_dropdown.grid(row=2, column=1, padx=5, pady=5, sticky="EW")
timestamp_dropdown.bind("<<ComboboxSelected>>", on_timestamp_select)

btn_previous = ttk.Button(frame, text="Précédent", command=select_previous_timestamp)
btn_previous.grid(row=4, column=0, padx=5, pady=5, sticky="EW")

btn_next = ttk.Button(frame, text="Suivant", command=select_next_timestamp)
btn_next.grid(row=4, column=1, padx=5, pady=5, sticky="EW")

text_area = tk.Text(frame, height=10, width=80)
text_area.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="EW")

btn_bras_droit = ttk.Button(frame, text="Bras Droit", command=lambda: save_label("bras_droit"))
btn_bras_droit.grid(row=5, column=0, padx=5, pady=5, sticky="EW")

btn_bras_gauche = ttk.Button(frame, text="Bras Gauche", command=lambda: save_label("bras_gauche"))
btn_bras_gauche.grid(row=5, column=2, padx=5, pady=5, sticky="EW")

btn_vide = ttk.Button(frame, text="Label Vide", command=lambda: save_label(""))
btn_vide.grid(row=5, column=1, padx=5, pady=5, sticky="EW")

file_label = ttk.Label(frame, text="Aucun fichier choisi")
file_label.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="EW")

mp4_file_label = ttk.Label(frame, text="Aucun fichier MP4 choisi")
mp4_file_label.grid(row=1, column=1, padx=5, pady=5, sticky="EW")

frame.columnconfigure(0, weight=1)
frame.columnconfigure(1, weight=2)

grid_frame = ttk.Frame(root)
grid_frame.grid(row=1, column=0, sticky="NSEW", padx=10, pady=10)

image_label = ttk.Label(root)
image_label.grid(row=1, column=1, columnspan=3, padx=5, pady=5)

grid_labels = []
for row in range(8):
    row_labels = []
    for col in range(8):
        label = tk.Label(grid_frame, text="", width=4, height=2, borderwidth=1, relief="solid", font=("Arial", 10))
        label.grid(row=row, column=col, padx=2, pady=2)
        row_labels.append(label)
    grid_labels.append(row_labels)

root.columnconfigure(0, weight=1)
root.rowconfigure(1, weight=1)

root.mainloop()
