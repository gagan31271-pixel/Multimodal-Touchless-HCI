import ctypes
import json
import os
import time
from pathlib import Path

import cv2
from deepface import DeepFace


PROJECT_ROOT = Path(__file__).resolve().parents[2]
AUTH_DIR = PROJECT_ROOT / "data" / "face_auth"
REGISTERED_FACE = AUTH_DIR / "registered_face.jpg"
AUTH_CONFIG = AUTH_DIR / "auth_config.json"

CAMERA_INDEX = 0
FACE_MODEL = "Facenet512"
DETECTOR_BACKEND = "opencv"
DISTANCE_METRIC = "cosine"
VERIFICATION_THRESHOLD = 0.30

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600

SW_RESTORE = 9
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_SHOWWINDOW = 0x0040


class FaceAuthentication:
    def __init__(self):
        AUTH_DIR.mkdir(parents=True, exist_ok=True)

    def _bring_window_to_front(self, window_title):
        """Attempt to activate and foreground the OpenCV window on Windows."""
        try:
            user32 = ctypes.windll.user32
            hwnd = user32.FindWindowW(None, window_title)

            if not hwnd:
                return False

            user32.ShowWindow(hwnd, SW_RESTORE)

            # Temporarily place the window above other windows.
            user32.SetWindowPos(
                hwnd,
                HWND_TOPMOST,
                0,
                0,
                0,
                0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW,
            )

            user32.SetForegroundWindow(hwnd)
            user32.BringWindowToTop(hwnd)
            user32.SetActiveWindow(hwnd)
            user32.SetFocus(hwnd)

            # Remove permanent topmost status while preserving visibility.
            user32.SetWindowPos(
                hwnd,
                HWND_NOTOPMOST,
                0,
                0,
                0,
                0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW,
            )

            return True

        except Exception:
            return False

    def _capture_face(self, window_title):
        """Capture a face with a visible OpenCV camera window."""

        camera = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)

        if not camera.isOpened():
            camera.release()
            raise RuntimeError(
                "Unable to open the camera. Close other applications "
                "using it and check Windows camera permissions."
            )

        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        captured_image = None
        window_created = False
        last_activation = 0.0

        try:
            cv2.namedWindow(window_title, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(window_title, WINDOW_WIDTH, WINDOW_HEIGHT)
            window_created = True

            # Wait for the first valid camera frame.
            frame = None

            for _ in range(30):
                success, candidate = camera.read()

                if success and candidate is not None:
                    frame = candidate
                    break

                cv2.waitKey(50)

            if frame is None:
                raise RuntimeError(
                    "The camera opened but did not provide frames. "
                    "Close other camera applications and try again."
                )

            cv2.imshow(window_title, frame)
            cv2.waitKey(150)

            # Retry activation while the window is being created.
            for _ in range(8):
                self._bring_window_to_front(window_title)
                cv2.waitKey(100)

            while True:
                success, frame = camera.read()

                if not success or frame is None:
                    raise RuntimeError(
                        "Unable to read a camera frame. "
                        "Check whether another application is using the camera."
                    )

                display = frame.copy()

                cv2.putText(
                    display,
                    "SPACE: Capture | Q: Cancel",
                    (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                )

                cv2.putText(
                    display,
                    "Position your face inside the camera view",
                    (20, 70),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2,
                )

                cv2.imshow(window_title, display)

                key = cv2.waitKey(10) & 0xFF

                # If Windows leaves the window behind, retry activation
                # at a short interval instead of continuously stealing focus.
                now = time.monotonic()

                if now - last_activation > 1.0:
                    self._bring_window_to_front(window_title)
                    last_activation = now

                if key == ord(" "):
                    captured_image = frame.copy()
                    break

                if key in (ord("q"), 27):
                    break

        finally:
            camera.release()

            if window_created:
                try:
                    cv2.destroyWindow(window_title)
                    cv2.waitKey(1)
                except cv2.error:
                    pass

        return captured_image

    def is_registered(self):
        return REGISTERED_FACE.is_file()

    def get_registered_username(self):
        if not AUTH_CONFIG.is_file():
            return "authorized_user"

        try:
            metadata = json.loads(
                AUTH_CONFIG.read_text(encoding="utf-8")
            )
            return metadata.get("username", "authorized_user")
        except (OSError, ValueError):
            return "authorized_user"

    def register_face(self, username="authorized_user"):
        temporary_path = AUTH_DIR / "registration_temp.jpg"

        try:
            image = self._capture_face("Face Registration")

            if image is None:
                return {
                    "success": False,
                    "message": "Face registration cancelled.",
                }

            faces = DeepFace.extract_faces(
                img_path=image,
                detector_backend=DETECTOR_BACKEND,
                enforce_detection=True,
                align=True,
            )

            if not faces:
                return {
                    "success": False,
                    "message": "No face detected. Please try again.",
                }

            if not cv2.imwrite(str(temporary_path), image):
                return {
                    "success": False,
                    "message": "Could not save the captured image.",
                }

            os.replace(temporary_path, REGISTERED_FACE)

            metadata = {
                "username": username,
                "registered_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "model": FACE_MODEL,
                "detector_backend": DETECTOR_BACKEND,
            }

            AUTH_CONFIG.write_text(
                json.dumps(metadata, indent=4),
                encoding="utf-8",
            )

            return {
                "success": True,
                "message": f"Face registered successfully for {username}.",
            }

        except Exception as error:
            return {
                "success": False,
                "message": f"Registration failed: {error}",
            }

        finally:
            if temporary_path.exists():
                try:
                    temporary_path.unlink()
                except OSError:
                    pass

    def verify_face(self):
        if not self.is_registered():
            return {
                "authenticated": False,
                "message": "No face is registered.",
                "distance": None,
            }

        try:
            live_image = self._capture_face("Face Verification")

            if live_image is None:
                return {
                    "authenticated": False,
                    "message": "Verification cancelled.",
                    "distance": None,
                }

            result = DeepFace.verify(
                img1_path=str(REGISTERED_FACE),
                img2_path=live_image,
                model_name=FACE_MODEL,
                detector_backend=DETECTOR_BACKEND,
                distance_metric=DISTANCE_METRIC,
                enforce_detection=True,
                align=True,
                threshold=VERIFICATION_THRESHOLD,
            )

            distance = float(result.get("distance", 1.0))
            verified = bool(result.get("verified", False))

            return {
                "authenticated": verified,
                "message": (
                    "Identity verified."
                    if verified
                    else "Face verification failed. Access denied."
                ),
                "distance": distance,
            }

        except Exception as error:
            return {
                "authenticated": False,
                "message": f"Verification failed: {error}",
                "distance": None,
            }

