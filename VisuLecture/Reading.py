import datetime
import os
import sys, cv2, pyvirtualcam

from eyetrax import GazeEstimator, run_9_point_calibration
import csv

# --- CLI ---
if len(sys.argv) < 2:
    print("Usage: vcam_worker.py <video_path> [fps]")
    sys.exit(1)

video_path = sys.argv[1]
csv_path = sys.argv[2]
list_points = []


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
            x, y = estimator.predict([features])[0]
            list_points.append((datetime.datetime.now().timestamp(), round(x), round(y)))

    cap.release()


try:
    print("Début de l'enregistrement du regard...")
    record_gaze(video_path)
    print("Enregistrement terminé. Sauvegarde des données dans le fichier CSV...")
    record_to_csv(list_points, csv_path)
    print(f"Enregistrement terminé. Données sauvegardées dans {csv_path}")
except Exception as e:
    print("Erreur durant la lecture :", e)