import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox

def select_csv():
    """Permet de sélectionner un fichier CSV."""
    filepath = filedialog.askopenfilename(
        title="Sélectionnez un fichier CSV",
        filetypes=[("Fichiers CSV", "*.csv"), ("Tous les fichiers", "*.*")]
    )
    if filepath:
        csv_label.config(text=f"Fichier CSV : {filepath}")
    else:
        csv_label.config(text="Aucun fichier sélectionné")

def select_video():
    """Permet de sélectionner un fichier vidéo."""
    filepath = filedialog.askopenfilename(
        title="Sélectionnez une vidéo",
        filetypes=[("Fichiers vidéo", "*.mp4 *.avi *.mov *.mkv"), ("Tous les fichiers", "*.*")]
    )
    if filepath:
        video_label.config(text=f"Fichier vidéo : {filepath}")
    else:
        video_label.config(text="Aucun fichier sélectionné")

# Création de la fenêtre principale
root = tk.Tk()
root.title("Sélectionner des fichiers")

# Ajout des widgets
csv_button = tk.Button(root, text="Sélectionner un fichier CSV", command=select_csv)
csv_button.pack(pady=10)

csv_label = tk.Label(root, text="Aucun fichier sélectionné", wraplength=400, justify="left")
csv_label.pack(pady=5)

video_button = tk.Button(root, text="Sélectionner une vidéo", command=select_video)
video_button.pack(pady=10)

video_label = tk.Label(root, text="Aucun fichier sélectionné", wraplength=400, justify="left")
video_label.pack(pady=5)

# Lancement de la boucle principale
root.mainloop()
