import datetime
import subprocess
import os
import psutil
import pyautogui
from pywinauto.application import Application
from pywinauto import Desktop
import sys, time, cv2, pyvirtualcam
import threading

# --- CLI ---
if len(sys.argv) < 2:
    print("Usage: vcam_worker.py <video_path> [fps]")
    sys.exit(1)

video_path = sys.argv[1]
target_fps = float(sys.argv[2]) if len(sys.argv) > 2 else 30.0

# --- CACHE VIDEO CONFIG (constante) ---
CACHE_VIDEO_NAME = "reading.webm"
CACHE_VIDEO_PATH = os.path.join(video_path, CACHE_VIDEO_NAME)

# Variable de contrôle (demandée)
stop_cache_video = False

def play_cache_video(video_path: str, target_fps: float, cam):
    """Joue une vidéo 'cache' en boucle tant que stop_cache_video est False."""
    global stop_cache_video

    while not stop_cache_video:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Cannot open cache video: {video_path}")
            return

        try:
            while not stop_cache_video:
                ok, frame = cap.read()
                if not ok:
                    break  # on repart du début de la vidéo cache

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                cam.send(rgb)
                cam.sleep_until_next_frame()
        finally:
            cap.release()

def play_video(video_path: str, target_fps: float = 30.0, point=(50,50,50), cam=None):
    """Lit le fichier vidéo et l'envoie à la caméra virtuelle.
    Déclenche video_done quand la lecture est terminée.
    """

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open {video_path}")

    ok, frame = cap.read()
    if not ok:
        cap.release()
        raise RuntimeError("Empty video")

    h, w = frame.shape[:2]
    try:
        # Repars du début
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        print("début", datetime.datetime.now())
        while True:
            ok, frame = cap.read()
            if not ok:
                pyautogui.moveTo(point[1], point[2], duration=0)
                pyautogui.click()
                time.sleep(1)
                break  # fin de vidéo
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            cam.send(rgb)
            cam.sleep_until_next_frame()# cadence régulière
        print("Video playback done.", datetime.datetime.now())

        time.sleep(1)
    finally:
        cap.release()

def initCam(video_path: str, target_fps: float = 30.0, point=(50,50,50), cam=None):
    """Lit le fichier vidéo et l'envoie à la caméra virtuelle.
    Déclenche video_done quand la lecture est terminée.
    """

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open {video_path}")

    ok, frame = cap.read()
    if not ok:
        cap.release()
        raise RuntimeError("Empty video")

    h, w = frame.shape[:2]
    try:
        # Repars du début
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        print("début", datetime.datetime.now())

        while True:
            ok, frame = cap.read()
            if not ok:
                time.sleep(1)

                # Récupérer le panneau latéral principal
                panel = Desktop(backend="uia").window(title_re=".*BeamEye.*", found_index=0)
                panel.wait("visible enabled ready", timeout=60)

                # Cliquer sur le bouton "Calibrer"
                btn = panel.child_window(
                    auto_id="QApplication.SenseTrayMenu.TrayMenuMainFrame.QStackedWidget.QFrame.TrayMenuExtensionsAPIRowBoxWidget.AnimatedToggle",
                    control_type="CheckBox"
                )

                btn.wait("visible enabled ready", timeout=10)

                # On active seulement si c’est décoché
                state = btn.get_toggle_state()   # 0 = off, 1 = on

                if state == 0:
                    btn.click_input()

                # Cliquer sur le bouton "Calibrer"
                btn = panel.child_window(title="Calibrer", control_type="Button")
                btn.wait("visible enabled ready", timeout=10)
                btn.click_input()

                panel = Desktop(backend="uia").window(title_re=".*Calibration.*")
                panel.wait("visible enabled ready", timeout=15)
                break  # fin de vidéo
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            cam.send(rgb)
            cam.sleep_until_next_frame()# cadence régulière
        print("Video playback done.", datetime.datetime.now())

        time.sleep(1)
    finally:
        #cap.release()
        pass

def click(camera):
    screen_width, screen_height = pyautogui.size()

    points = [
        (0, screen_width // 2, screen_height // 2),
        (1, 50, 50),
        (2, screen_width - 50, 50),
        (3, screen_width - 50, screen_height - 50),
        (4, 50, screen_height - 50),
    ]

    for point in points:
        play_video(video_path + "video" + str(point[0]) + ".webm", target_fps, point, cam)

        #pyautogui.moveTo(point[1], point[2], duration=0)
        #pyautogui.click()

def openBeamEye():
    # Chemin de BeamEye.exe
    path = r"C:\Program Files\Eyeware\BeamEyeTracker\BeamEyeTracker.exe"
    folder = os.path.dirname(path)

    subprocess.Popen(
        [path],
        cwd=folder,
        creationflags=0x08000000  # CREATE_NO_WINDOW
    )

    app = Application(backend="uia").connect(path=path)

def closeBeamEye():
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == 'BeamEyeTracker.exe':
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except psutil.TimeoutExpired:
                proc.kill()

tryCalib = True
cam = None

while (tryCalib):
    try:
        openBeamEye()

        cap = cv2.VideoCapture(video_path + "video0.webm")
        _, firstFrame = cap.read()
        h, w = firstFrame.shape[:2]

        cam = pyvirtualcam.Camera(width=w, height=h, fps=target_fps, print_fps=False, device="Unity Video Capture")

        # --- Démarrage vidéo cache tant que click() n'a pas commencé ---
        stop_cache_video = False
        cache_thread = threading.Thread(
            target=play_cache_video,
            args=(CACHE_VIDEO_PATH, target_fps, cam),
            daemon=True
        )
        cache_thread.start()

        initCam(video_path + "video0.webm", target_fps, cam=cam)

        # --- Stop cache juste avant click() ---
        stop_cache_video = True
        time.sleep(0.2)  # laisse le thread sortir proprement

        click(cam)

        cam.close()

        tryCalib = False
    except Exception as e:
        print("Erreur durant la calibration :", e)
        closeBeamEye()
        stop_cache_video = True
        if cam is not None:
            cam.close()
