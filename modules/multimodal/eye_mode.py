from __future__ import annotations

import cv2
import pyautogui

from modules.face_analysis.face_detector import FaceDetector
from modules.face_analysis.blink_detector import BlinkDetector


class EyeMode:
    """
    Eye/Wink interaction mode.

    Left wink  -> Left click
    Right wink -> Right click

    Face expression detection is NOT used here.
    """

    WINDOW_NAME = "Multimodal Touchless HCI - Eye Mode"

    def __init__(self, camera_index: int = 0) -> None:

        self.camera_index = camera_index

        self.face_detector = FaceDetector()
        self.blink_detector = BlinkDetector()

        self.cap = None
        self.running = False
        self.last_wink = "NONE"
        self.last_action = "None"
        self.eye_status = "Waiting"

    # ============================================================
    # EXTRACT LANDMARK SEQUENCE
    # ============================================================

    @staticmethod
    def _extract_landmarks(face_result):
        """
        BlinkDetector expects the landmark sequence itself.
        MediaPipe normally wraps it inside NormalizedLandmarkList.
        """

        if face_result is None:
            return None

        # Normal MediaPipe Face Mesh result
        face_list = getattr(
            face_result,
            "multi_face_landmarks",
            None,
        )

        if face_list:
            return list(face_list[0].landmark)

        # Some wrappers may return a tuple
        if isinstance(face_result, tuple):

            for item in face_result:

                if item is None:
                    continue

                face_list = getattr(
                    item,
                    "multi_face_landmarks",
                    None,
                )

                if face_list:
                    return list(face_list[0].landmark)

                if hasattr(item, "landmark"):
                    return list(item.landmark)

        # Already a landmark list
        if hasattr(face_result, "landmark"):
            return list(face_result.landmark)

        return None

    # ============================================================
    # NORMALIZE WINK RESULT
    # ============================================================

    @staticmethod
    def _normalize_wink(result) -> str:

        if result is None:
            return "NONE"

        if isinstance(result, str):
            value = result.strip().lower()

        elif isinstance(result, dict):

            value = ""

            for key in (
                "wink",
                "action",
                "gesture",
                "result",
            ):

                if key in result:
                    value = str(
                        result[key]
                    ).strip().lower()
                    break

            if not value:
                value = str(result).lower()

        else:
            value = str(result).strip().lower()

        if (
            "left" in value
            and "wink" in value
        ):
            return "LEFT_WINK"

        if (
            "right" in value
            and "wink" in value
        ):
            return "RIGHT_WINK"

        if value in {
            "left",
            "left_eye",
        }:
            return "LEFT_WINK"

        if value in {
            "right",
            "right_eye",
        }:
            return "RIGHT_WINK"

        if (
            "both" in value
            or "closed" in value
            or "blink" == value
        ):
            return "NONE"

        return value.upper()

    # ============================================================
    # START
    # ============================================================

    def process_frame(self, frame, draw_landmarks: bool = True):
        """Process a supplied BGR frame without opening or owning a camera.

        The standalone ``start()`` loop remains available. The Streamlit
        dashboard calls this method from its single WebRTC camera processor.
        """
        if frame is None:
            return {"frame": frame, "wink": "NONE", "action": "None",
                    "eye_status": "No frame", "detected": False}

        frame = cv2.flip(frame, 1)
        face_result = self.face_detector.process(frame)
        if draw_landmarks:
            try:
                self.face_detector.draw_landmarks(frame, face_result)
            except Exception:
                pass

        landmarks = self._extract_landmarks(face_result)
        wink = "NONE"
        action = "None"
        if landmarks is not None:
            try:
                wink = self._normalize_wink(
                    self.blink_detector.detect_wink(landmarks)
                )
                if wink == "LEFT_WINK":
                    pyautogui.click(button="left")
                    action = "Left Click"
                elif wink == "RIGHT_WINK":
                    pyautogui.click(button="right")
                    action = "Right Click"
                else:
                    action = getattr(self.blink_detector, "last_action", "None")
            except Exception as exc:
                wink = "ERROR"
                action = f"Detection error: {exc}"
        else:
            try:
                self.blink_detector.reset()
            except Exception:
                pass

        self.last_wink = wink
        self.last_action = action
        self.eye_status = "Face detected" if landmarks is not None else "No face detected"

        # Draw a readable status panel directly on the live camera frame.
        # The dashboard displays this returned, annotated frame through WebRTC.
        panel_width = min(520, max(360, frame.shape[1] - 20))
        cv2.rectangle(
            frame,
            (10, 10),
            (panel_width, 116),
            (20, 20, 20),
            -1,
        )

        if landmarks is None:
            wink_label = "Eye movement: Waiting for face"
            action_label = "Action: None"
        elif wink == "LEFT_WINK":
            wink_label = "Eye movement: LEFT WINK"
            action_label = "Action: LEFT CLICK"
        elif wink == "RIGHT_WINK":
            wink_label = "Eye movement: RIGHT WINK"
            action_label = "Action: RIGHT CLICK"
        elif wink == "ERROR":
            wink_label = "Eye movement: Detection error"
            action_label = f"Action: {action}"
        else:
            wink_label = "Eye movement: Neutral / normal blink"
            action_label = f"Action: {action}"

        cv2.putText(
            frame,
            f"Status: {self.eye_status}",
            (20, 38),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.58,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            wink_label,
            (20, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.58,
            (0, 255, 255),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            action_label[:58],
            (20, 101),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.58,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )

        return {
            "frame": frame,
            "wink": wink,
            "action": action,
            "eye_status": self.eye_status,
            "detected": landmarks is not None,
        }

    def start(self) -> None:

        self.cap = cv2.VideoCapture(
            self.camera_index
        )

        if not self.cap.isOpened():

            raise RuntimeError(
                f"Unable to open camera "
                f"{self.camera_index}."
            )

        self.cap.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            640,
        )

        self.cap.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            480,
        )

        self.cap.set(
            cv2.CAP_PROP_BUFFERSIZE,
            1,
        )

        self.running = True

        print("=" * 65)
        print("EYE / WINK MODE")
        print("=" * 65)
        print("Left wink  -> Left click")
        print("Right wink -> Right click")
        print("Press ESC or Q to stop.")
        print("=" * 65)

        try:

            while self.running:

                success, frame = (
                    self.cap.read()
                )

                if not success:
                    continue

                frame = cv2.flip(
                    frame,
                    1,
                )

                # ------------------------------------------------
                # FACE DETECTION
                # ------------------------------------------------

                face_result = (
                    self.face_detector.process(
                        frame
                    )
                )

                try:

                    self.face_detector.draw_landmarks(
                        frame,
                        face_result,
                    )

                except Exception:
                    pass

                # ------------------------------------------------
                # GET CORRECT LANDMARK LIST
                # ------------------------------------------------

                landmarks = (
                    self._extract_landmarks(
                        face_result
                    )
                )

                wink = "NONE"

                if landmarks is not None:

                    try:

                        result = (
                            self.blink_detector.detect_wink(
                                landmarks
                            )
                        )

                        wink = (
                            self._normalize_wink(
                                result
                            )
                        )

                    except Exception as exc:

                        wink = "ERROR"

                        print(
                            f"[EYE] Detection error: {exc}"
                        )

                else:

                    try:
                        self.blink_detector.reset()
                    except Exception:
                        pass

                # ------------------------------------------------
                # ACTION
                # ------------------------------------------------

                if wink == "LEFT_WINK":

                    pyautogui.click(
                        button="left"
                    )

                    print(
                        "[EYE] LEFT WINK -> LEFT CLICK"
                    )

                elif wink == "RIGHT_WINK":

                    pyautogui.click(
                        button="right"
                    )

                    print(
                        "[EYE] RIGHT WINK -> RIGHT CLICK"
                    )

                # ------------------------------------------------
                # DISPLAY
                # ------------------------------------------------

                face_status = (
                    "Face detected" if landmarks is not None else "No face detected"
                )
                if wink == "LEFT_WINK":
                    action_status = "Action: LEFT CLICK"
                    movement_status = "Eye movement: LEFT WINK"
                elif wink == "RIGHT_WINK":
                    action_status = "Action: RIGHT CLICK"
                    movement_status = "Eye movement: RIGHT WINK"
                elif wink == "ERROR":
                    action_status = "Action: Detection error"
                    movement_status = "Eye movement: ERROR"
                else:
                    action_status = "Action: None"
                    movement_status = "Eye movement: Neutral / normal blink"

                cv2.rectangle(
                    frame,
                    (10, 10),
                    (min(520, max(360, frame.shape[1] - 20)), 116),
                    (20, 20, 20),
                    -1,
                )
                cv2.putText(
                    frame,
                    f"Status: {face_status}",
                    (20, 38),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.58,
                    (255, 255, 255),
                    2,
                    cv2.LINE_AA,
                )
                cv2.putText(
                    frame,
                    movement_status,
                    (20, 70),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.58,
                    (0, 255, 255),
                    2,
                    cv2.LINE_AA,
                )
                cv2.putText(
                    frame,
                    action_status,
                    (20, 101),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.58,
                    (255, 255, 255),
                    2,
                    cv2.LINE_AA,
                )

                cv2.imshow(
                    self.WINDOW_NAME,
                    frame,
                )

                key = (
                    cv2.waitKey(1)
                    & 0xFF
                )

                if key in (
                    27,
                    ord("q"),
                ):

                    self.stop()

        finally:

            self.stop()

    # ============================================================
    # STOP
    # ============================================================

    def stop(self) -> None:

        self.running = False

        try:
            self.blink_detector.reset()
        except Exception:
            pass

        if self.cap is not None:

            self.cap.release()
            self.cap = None

        cv2.destroyAllWindows()

        try:
            self.face_detector.close()
        except Exception:
            pass

        print(
            "[EYE] Eye Mode stopped."
        )


def run_eye_mode() -> None:

    app = EyeMode()

    try:

        app.start()

    except KeyboardInterrupt:

        print(
            "\n[EYE] Interrupted."
        )

    finally:

        app.stop()


if __name__ == "__main__":
    run_eye_mode()
