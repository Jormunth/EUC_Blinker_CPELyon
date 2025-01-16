import cv2
import os

def extract_frames_with_timestamps(mp4_filepath):
    # Vérification que le fichier vidéo existe
    if not os.path.exists(mp4_filepath):
        print(f"Erreur: Le fichier {mp4_filepath} n'existe pas.")
        return
    
    # Ouverture du fichier vidéo
    cap = cv2.VideoCapture(mp4_filepath)
    
    if not cap.isOpened():
        print(f"Erreur: Impossible d'ouvrir la vidéo {mp4_filepath}.")
        return
    
    # Récupération du nombre total de frames et du taux de frames par seconde (FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    print(f"Vidéo {mp4_filepath} chargée avec succès. Total des frames : {total_frames}, FPS : {fps:.2f}")
    
    # Itération sur chaque frame
    frame_number = 0
    while True:
        ret, frame = cap.read()  # Lecture d'une frame
        if not ret:
            break  # Fin de la vidéo
        
        # Calcul du timestamp basé sur le numéro de frame et le FPS
        timestamp = frame_number / fps
        timestamp_str = f"{int(timestamp // 3600):02}:{int((timestamp % 3600) // 60):02}:{int(timestamp % 60):02}.{int((timestamp % 1) * 1000000):06}"
        
        # Affichage du numéro de frame et du timestamp correspondant
        print(f"Frame {frame_number + 1} -> Timestamp : {timestamp_str}")
        
        frame_number += 1
    
    cap.release()  # Fermeture du fichier vidéo

if __name__ == "__main__":
    mp4_filepath = input("Entrez le chemin du fichier vidéo MP4 : ")
    extract_frames_with_timestamps(mp4_filepath)
