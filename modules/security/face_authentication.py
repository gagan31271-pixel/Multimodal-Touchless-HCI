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

WINDOW_WIDTH = 600
WINDOW_HEIGHT = 400

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

    @staticmethod
    def _eye_aspect_ratio(landmarks, indexes, frame_width, frame_height):
        """Calculate EAR from six MediaPipe Face Mesh eye landmarks."""
        points = []
        for index in indexes:
            landmark = landmarks[index]
            points.append((
                int(landmark.x * frame_width),
                int(landmark.y * frame_height),
            ))

        vertical_1 = cv2.norm(
            (points[1][0] - points[5][0], points[1][1] - points[5][1])
        )
        vertical_2 = cv2.norm(
            (points[2][0] - points[4][0], points[2][1] - points[4][1])
        )
        horizontal = cv2.norm(
            (points[0][0] - points[3][0], points[0][1] - points[3][1])
        )

        if horizontal <= 0:
            return 0.0

        return (vertical_1 + vertical_2) / (2.0 * horizontal)

    def _capture_face(self, window_title):
        """
        Capture only when exactly one face is visible.

        A double blink can trigger capture. SPACE is also supported as a manual
        capture shortcut, but SPACE alone is not proof of liveness.
        """
        try:
            import mediapipe as mp
        except ImportError as exc:
            raise RuntimeError(
                "MediaPipe is required for live face and blink detection. "
                "Install it in this project's virtual environment."
            ) from exc

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

        # MediaPipe Face Mesh provides both face count and eye landmarks.
        face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=2,
            refine_landmarks=True,
            min_detection_confidence=0.55,
            min_tracking_confidence=0.55,
        )

        # MediaPipe Face Mesh landmark indices for the eye contours.
        left_eye = (33, 160, 158, 133, 153, 144)
        right_eye = (362, 385, 387, 263, 373, 380)
        ear_threshold = 0.20
        closed_frames_required = 2
        closed_frames = 0
        eye_was_closed = False
        blink_count = 0
        last_blink_time = 0.0
        double_blink_window = 2.0
        blink_cooldown = 0.0

        try:
            cv2.namedWindow(window_title, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(window_title, WINDOW_WIDTH, WINDOW_HEIGHT)
            window_created = True

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

            for _ in range(8):
                self._bring_window_to_front(window_title)
                cv2.waitKey(100)

            while True:
                success, frame = camera.read()
                if not success or frame is None:
                    raise RuntimeError(
                        "Unable to read a camera frame. Check whether another "
                        "application is using the camera."
                    )

                height, width = frame.shape[:2]
                display = frame.copy()
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                result = face_mesh.process(rgb)
                faces = result.multi_face_landmarks or []
                now = time.monotonic()

                if len(faces) == 0:
                    status = "No face detected - move into view"
                    status_color = (0, 0, 255)
                    blink_count = 0
                    closed_frames = 0
                    eye_was_closed = False

                elif len(faces) > 1:
                    status = "Multiple faces detected - only one person allowed"
                    status_color = (0, 0, 255)
                    blink_count = 0
                    closed_frames = 0
                    eye_was_closed = False

                    for face in faces:
                        xs = [int(point.x * width) for point in face.landmark]
                        ys = [int(point.y * height) for point in face.landmark]
                        cv2.rectangle(
                            display,
                            (max(0, min(xs)), max(0, min(ys))),
                            (min(width - 1, max(xs)), min(height - 1, max(ys))),
                            (0, 0, 255),
                            2,
                        )

                else:
                    landmarks = faces[0].landmark
                    xs = [int(point.x * width) for point in landmarks]
                    ys = [int(point.y * height) for point in landmarks]
                    x1, y1 = max(0, min(xs)), max(0, min(ys))
                    x2, y2 = min(width - 1, max(xs)), min(height - 1, max(ys))

                    left_ear = self._eye_aspect_ratio(
                        landmarks, left_eye, width, height
                    )
                    right_ear = self._eye_aspect_ratio(
                        landmarks, right_eye, width, height
                    )
                    average_ear = (left_ear + right_ear) / 2.0
                    eyes_closed = average_ear < ear_threshold

                    cv2.rectangle(
                        display, (x1, y1), (x2, y2), (0, 200, 0), 2
                    )

                    if eyes_closed:
                        closed_frames += 1
                    else:
                        if (
                            eye_was_closed
                            and closed_frames >= closed_frames_required
                            and now - blink_cooldown > 0.25
                        ):
                            if now - last_blink_time <= double_blink_window:
                                blink_count += 1
                            else:
                                blink_count = 1
                            last_blink_time = now
                            blink_cooldown = now

                        closed_frames = 0

                    eye_was_closed = eyes_closed

                    if blink_count >= 2:
                        captured_image = frame.copy()
                        break

                    status = (
                        "1 face detected - blink twice or press SPACE"
                        if not eyes_closed
                        else "Blink detected - blink twice"
                    )
                    status_color = (0, 200, 0)

                cv2.putText(
                    display,
                    status,
                    (15, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.58,
                    status_color,
                    2,
                    cv2.LINE_AA,
                )
                cv2.putText(
                    display,
                    f"Double blinks: {blink_count}/2",
                    (15, 60),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 0),
                    2,
                    cv2.LINE_AA,
                )
                cv2.putText(
                    display,
                    "SPACE: Capture | Q / ESC: Cancel",
                    (15, height - 18),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    2,
                    cv2.LINE_AA,
                )

                cv2.imshow(window_title, display)
                key = cv2.waitKey(10) & 0xFF

                if now - last_activation > 1.0:
                    self._bring_window_to_front(window_title)
                    last_activation = now

                # Manual capture is allowed only when exactly one face is visible.
                if key == ord(" ") and len(faces) == 1:
                    captured_image = frame.copy()
                    break

                if key in (ord("q"), 27):
                    break

        finally:
            face_mesh.close()
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

