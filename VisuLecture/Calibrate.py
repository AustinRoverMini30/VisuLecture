"""
Demo de calibration sans interface graphique.
Utilise un flux vidéo (webcam ou webcam virtuelle) pour calibrer le modèle.
"""
import argparse
import time
from pathlib import Path

import cv2
import numpy as np

from eyetrax.calibration.common import compute_grid_points
from eyetrax.gaze import GazeEstimator
from eyetrax.utils.screen import get_screen_size

def     run_headless_calibration(
        gaze_estimator,
        calibration_points: str = "9p",
        capture_duration: float = 2.0,
        screen_size: tuple = None,
        video_paths: list = None,
):
    """
    Effectue une calibration sans interface graphique.

    Args:
        gaze_estimator: Instance de GazeEstimator
        calibration_points: Type de calibration ("9p", "5p", "center")
        capture_duration: Durée de capture par point (secondes)
        screen_size: Tuple (width, height) de la résolution d'écran
        video_paths: Liste des chemins vers les vidéos de calibration
    """
    sw, sh = get_screen_size() if screen_size is None else screen_size

    # Définir les points de calibration
    if calibration_points == "9p":
        order = [
            (1, 1), (0, 0), (2, 0), (0, 2), (2, 2),
            (1, 0), (0, 1), (2, 1), (1, 2),
        ]
    elif calibration_points == "5p":
        order = [(1, 1), (0, 0), (2, 0), (2, 2), (0, 2)]
    elif calibration_points == "center":
        order = [(1, 1)]  # Point central uniquement
    else:
        raise ValueError(f"Type de calibration inconnu: {calibration_points}")

    pts = compute_grid_points(order, sw, sh)

    res = analyze_from_videos(gaze_estimator, video_paths, pts)
    if res is None:
        return
    feats, targs = res
    if feats:
        gaze_estimator.train(np.array(feats), np.array(targs))

    return True


def maint():
    parser = argparse.ArgumentParser(
        description="Calibration headless pour EyeTrax via webcam virtuelle"
    )
    parser.add_argument(
        "--video-prefix",
        type=str,
        help="Préfixe du chemin des vidéos (ex: 'uploads/bidule/video' pour video0.webm, video1.webm, ...)"
    )
    parser.add_argument(
        "--calibration",
        choices=["9p", "5p", "center"],
        default="9p",
        help="Type de calibration: 9 points, 5 points, ou centre uniquement"
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=2.0,
        help="Durée de capture par point (secondes)"
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1920,
        help="Largeur de l'écran"
    )
    parser.add_argument(
        "--height",
        type=int,
        default=1080,
        help="Hauteur de l'écran"
    )

    parser.add_argument(
        "--model",
        type=str,
        help="['elastic_net', 'linear_svr', 'ridge', 'svr', 'tiny_mlp']"
    )

    args = parser.parse_args()

    # Construire la liste des chemins vidéo
    num_videos = 9 if args.calibration == "9p" else (5 if args.calibration == "5p" else 1)
    video_paths = [f"{args.video_prefix}{i}.webm" for i in range(num_videos)]

    print(f"Chemins des vidéos générés:")
    for i, path in enumerate(video_paths):
        print(f"  Video {i}: {path}")

    if (args.model == "none"):
        print("Aucun modèle spécifié, utilisation du modèle par défaut.")
        gaze_estimator = GazeEstimator()
    else:
        print("Modèle spécifié:", args.model)
        gaze_estimator = GazeEstimator(model_name=args.model)

    screen_size = (args.width, args.height)

    success = run_headless_calibration(
        gaze_estimator,
        calibration_points=args.calibration,
        capture_duration=args.duration,
        video_paths=video_paths,
        screen_size=screen_size
    )

    if success:
        output_file = f"gaze_model.pkl"
        gaze_estimator.save_model(output_file)
        print(f"Modèle sauvegardé: {output_file}")
    else:
        print("Calibration échouée. Aucun modèle sauvegardé.")

def analyze_from_videos(
        gaze_estimator,
        video_paths: list,
        pts,
        skip_frames: int = 30,
):
    """
    Analyze gaze from 5 videos (one per calibration point) without GUI.

    Args:
        gaze_estimator: The gaze estimator object
        video_paths: List of 5 video file paths
        pts: List of 5 calibration points [(x, y), ...]
        skip_frames: Number of initial frames to ignore per video

    Returns:
        Tuple of (features, targets) or None if error
    """
    if len(video_paths) != len(pts):
        raise ValueError(f"Number of videos ({len(video_paths)}) must match number of points ({len(pts)})")

    feats, targs = [], []

    for video_path, (x, y) in zip(video_paths, pts):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Error: Could not open video {video_path}")
            cap.release()
            return None

        # Skip initial frames
        for _ in range(skip_frames):
            cap.read()

        # Process remaining frames
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            ft, blink = gaze_estimator.extract_features(frame)
            if ft is not None and not blink:
                feats.append(ft)
                targs.append([x, y])

        cap.release()

    return feats, targs


if __name__ == "__main__":
    maint()