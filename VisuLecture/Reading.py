import datetime
import os
import sys, cv2, pyvirtualcam
import argparse
import numpy as np

from eyetrax import GazeEstimator, run_9_point_calibration
import csv

from eyetrax.filters import KDESmoother, NoSmoother

list_points = []

parser = argparse.ArgumentParser(
    description="Lecture pour EyeTrax via webcam virtuelle"
)

parser.add_argument(
    "--video",
    type=str
)

parser.add_argument(
    "--csv",
    type=str
)

parser.add_argument(
    "--filter",
    type=str
)

parser.add_argument(
    "--model",
    type=str
)

parser.add_argument(
    "--width",
    type=str
)

parser.add_argument(
    "--height",
    type=str
)

args = parser.parse_args()

video_path = args.video
csv_path = args.csv
filter = args.filter
screen_width, screen_height = args.width, args.height

def record_to_csv(data: list, csv_path: str):
    dir_path = os.path.dirname(csv_path)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)
    with open(csv_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['timestamp', 'x', 'y'])
        for timestamp, x, y in data:
            writer.writerow([timestamp, x, y])


def record_gaze(video_path: str):
    # Load model

    if args.model != "none":
        print("Modèle spécifié:", args.model)
        estimator = GazeEstimator(model_name=args.model)
    else:
        print("Aucun modèle spécifié, utilisation du modèle par défaut.")
        estimator = GazeEstimator()
    estimator.load_model("gaze_model.pkl")

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise ValueError(f"Impossible d'ouvrir la vidéo : {video_path}")

    while True:
        # Extract features from frame
        ret, frame = cap.read()

        if not ret or frame is None:
            break

        features, blink = estimator.extract_features(frame)

        # Predict screen coordinates
        if features is not None and not blink:
            gaze_point = estimator.predict(np.array([features]))[0]
            x, y = map(int, gaze_point)

            if filter == "kde":
                smoother = KDESmoother(screen_width, screen_height)
            else:
                smoother = NoSmoother()

            x_pred, y_pred = smoother.step(x, y)
            print(f"Gaze: ({x_pred}, {y_pred})")
            list_points.append((datetime.datetime.now().timestamp(), round(x_pred), round(y_pred)))

    cap.release()


try:
    print("Début de l'enregistrement du regard...")
    record_gaze(video_path)
    print("Enregistrement terminé. Sauvegarde des données dans le fichier CSV...")
    record_to_csv(list_points, csv_path)
    print(f"Enregistrement terminé. Données sauvegardées dans {csv_path}")
except Exception as e:
    print("Erreur durant la lecture :", e)