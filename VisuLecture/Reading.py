import datetime
import subprocess
import os
import psutil
from pywinauto.application import Application
from pywinauto import Desktop
import sys, cv2, pyvirtualcam

# --- CLI ---
if len(sys.argv) < 2:
    print("Usage: vcam_worker.py <video_path> [fps]")
    sys.exit(1)

video_path = sys.argv[1]
target_fps = float(sys.argv[2]) if len(sys.argv) > 2 else 30.0

def play_video(video_path: str, target_fps: float = 30.0):
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
        with pyvirtualcam.Camera(width=w, height=h, fps=target_fps, print_fps=False, device="Unity Video Capture") as cam:
            # Repars du début
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

            print("début", datetime.datetime.now())
            while True:
                ok, frame = cap.read()
                if not ok:
                    break  # fin de vidéo
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                cam.send(rgb)
                cam.sleep_until_next_frame()# cadence régulière
            print("Video playback done.", datetime.datetime.now())

        cam.close()
    finally:
        cap.release()

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

def click():
    play_video(video_path + "reading.webm", target_fps)

tryRead = True

while (tryRead):
    try:
        openBeamEye()
        # Récupérer le panneau latéral principal
        panel = Desktop(backend="uia").window(title_re=".*BeamEye.*", found_index=0)
        panel.wait("visible enabled ready", timeout=60)

        # Cliquer sur le bouton "Calibrer"
        btn = panel.child_window(
            auto_id="QApplication.SenseTrayMenu.TrayMenuMainFrame.QStackedWidget.QFrame.TrayMenuExtensionsAPIRowBoxWidget.AnimatedToggle",
            control_type="CheckBox"
        )

        btn.wait("visible enabled ready", timeout=10)

        # On récupère l'état ON/OFF
        try:
            state = btn.get_toggle_state()  # 0 = OFF, 1 = ON
        except:
            # fallback pour Qt si TogglePattern absent
            val = btn.get_value()
            state = 1 if str(val).lower() in ("true", "1") else 0

        # Si désactivé → on clique
        if state == 0:
            btn.click_input()

        click()

        tryRead = False
    except Exception as e:
        print("Erreur durant la lecture :", e)
        closeBeamEye()