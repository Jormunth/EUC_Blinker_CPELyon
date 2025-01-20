import pandas as pd
import numpy as np
import tensorflow as tf
import os
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.utils import to_categorical
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

# Partie 1 : Lecture et préparation des données
def load_and_prepare_data(csv_file):
    # Lire le fichier CSV
    data = pd.read_csv(csv_file, header=None)

    # Remplacement des valeurs non numériques (exemple: "X:X")
    data.replace({'X:X': 0, 'X': 0}, inplace=True)  # Ajoutez d'autres motifs si nécessaire

    # Conversion des colonnes d'entrée en type float, en gérant les erreurs
    try:
        features = data.iloc[:, :-1].apply(pd.to_numeric, errors='coerce').fillna(0)
    except Exception as e:
        print("Erreur lors de la conversion des features :", e)
        raise

    # Traitement des étiquettes (dernière colonne)
    labels = data.iloc[:, -1].astype(str)  # Convertir les étiquettes en chaînes si nécessaire
    label_encoder = LabelEncoder()
    encoded_labels = label_encoder.fit_transform(labels)
    categorical_labels = to_categorical(encoded_labels)  # Encodage one-hot

    return features, categorical_labels, label_encoder.classes_

    data = pd.read_csv(csv_file, header=None)
    data.replace({'X:X': 0}, inplace=True)  # Remplacement des valeurs "X:X" par 0
    features = data.iloc[:, :-1].astype(float)  # Colonnes d'entrée
    labels = data.iloc[:, -1]  # Dernière colonne
    label_encoder = LabelEncoder()
    encoded_labels = label_encoder.fit_transform(labels)
    categorical_labels = to_categorical(encoded_labels)  # Encodage one-hot
    return features, categorical_labels, label_encoder.classes_

# Partie 2 : Entraînement du réseau de neurones
def train_model(features, labels):
    input_dim = features.shape[1]
    output_dim = labels.shape[1]
    model = Sequential([
        Dense(128, input_dim=input_dim, activation='relu'),
        Dense(64, activation='relu'),
        Dense(output_dim, activation='softmax')
    ])
    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    model.fit(features, labels, epochs=10, batch_size=32, validation_split=0.2)
    return model

# Partie 3 : Conversion en TFLite et exportation pour STM32

def convert_to_tflite_and_export(model, output_dir):
    # Créer le répertoire de sortie s'il n'existe pas
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Répertoire créé : {output_dir}")

    # Convertir le modèle en TFLite
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    tflite_model = converter.convert()

    # Sauvegarder le modèle TFLite
    tflite_path = os.path.join(output_dir, "model.tflite")
    with open(tflite_path, "wb") as f:
        f.write(tflite_model)

    print(f"Modèle TFLite exporté vers : {tflite_path}")
    
    # Générer un fichier C
    with open(f"{output_dir}/model.cc", "w") as f:
        tflite_hex = ', '.join(f'0x{b:02x}' for b in tflite_model)
        f.write(f"""
#include <stddef.h>
#include <stdint.h>

const unsigned char model[] = {{ {tflite_hex} }};
const size_t model_len = {len(tflite_model)};
        """)

# Programme principal
if __name__ == "__main__":
    csv_file = "data.csv"  # Remplacez par le chemin de votre fichier CSV
    output_dir = "output"  # Répertoire de sortie

    # Charger et préparer les données
    features, labels, class_names = load_and_prepare_data(csv_file)
    print(f"Classes : {class_names}")

    # Entraîner le modèle
    model = train_model(features, labels)

    # Convertir et exporter
    convert_to_tflite_and_export(model, output_dir)
    print(f"Modèle exporté dans le répertoire {output_dir}.")
