from hachoir.parser import createParser
from hachoir.metadata import extractMetadata
from datetime import datetime

def get_creation_date_hachoir(mp4_filepath):
    """
    Récupère la date de création d'une vidéo MP4 à l'aide de hachoir.
    
    :param mp4_filepath: Chemin vers le fichier MP4
    :return: Date de création sous forme d'objet datetime ou None si non trouvée
    """
    try:
        # Crée un parser pour lire le fichier MP4
        parser = createParser(mp4_filepath)
        if not parser:
            print(f"Erreur : Impossible d'ouvrir le fichier {mp4_filepath}")
            return None
        
        # Extraire les métadonnées
        metadata = extractMetadata(parser)
        if not metadata:
            print("Erreur : Métadonnées introuvables.")
            return None
        
        # Chercher la date de création
        creation_date = metadata.get('creation_date')
        if creation_date:
            return creation_date
        else:
            print("Erreur : Date de création introuvable dans les métadonnées.")
            return None
    
    except Exception as e:
        print(f"Erreur lors de l'extraction des métadonnées : {e}")
        return None

if __name__ == "__main__":
    # Demander à l'utilisateur de fournir le chemin du fichier MP4
    mp4_path = input("Entrez le chemin du fichier MP4 : ")
    
    # Obtenir la date de création
    creation_date = get_creation_date_hachoir(mp4_path)
    
    if creation_date:
        print(f"Date de création de la vidéo : {creation_date}")
    else:
        print("Impossible de récupérer la date de création.")
