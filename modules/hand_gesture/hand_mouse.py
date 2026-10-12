"""
Hand Gesture Mouse Pipeline
---------------------------

Supports two execution modes:

1. Standalone mode
   Camera is opened internally and OpenCV window is displayed.

2. Dashboard mode
   Dashboard supplies webcam frames through process_frame().
   No camera is opened by this class.
   No OpenCV window is created.

Pipeline:

Frame
  ↓
HandDetector
  ↓
GestureClassifier
  ↓
CursorController
"""

from __future__ import annotations

import cv2

from .hand_detector import HandDetector
from .gesture_classifier import GestureClassifier, Gesture
from .cursor_controller import CursorController


class HandGestureMouse:
    """
    Complete hand gesture controller.

    Standalone:
        app = HandGestureMouse()
        app.start()

    Dashboard:
        app = HandGestureMouse(show_window=False)
        result = app.process_frame(frame)
    """

    WINDOW_NAME = "Multimodal Touchless HCI - Hand Gesture"

    def __init__(
        self,
        camera_index: int = 0,
        preferred_hand: str = "Right",
        show_window: bool = True,
    ) -> None:

        self.camera_index = camera_index
        self.preferred_hand = preferred_hand
        self.show_window = show_window

        # ----------------------------------------------------
        # HAND DETECTOR
        # ----------------------------------------------------

        self.detector = HandDetector(
            max_num_hands=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        # ----------------------------------------------------
        # GESTURE CLASSIFIER
        # ----------------------------------------------------

        self.classifier = GestureClassifier(
            stable_frames=4,
        )

        # ----------------------------------------------------
        # CURSOR CONTROLLER
        # ----------------------------------------------------

        self.controller = CursorController(
            smoothing_alpha=0.40,
            click_cooldown=0.45,
            scroll_cooldown=0.25,
            scroll_up_speed=6,
            scroll_down_speed=4,
        )

        # ----------------------------------------------------
        # CAMERA
        # ----------------------------------------------------

        self.cap = None
        self.running = False

        # ----------------------------------------------------
        # DASHBOARD STATUS
        # ----------------------------------------------------

        self.current_gesture = Gesture.NONE
        self.current_action = "None"
        self.current_hand = "None"

        self.last_results = None
        self.last_detected_hands = []

    # ========================================================
    # PROCESS ONE FRAME
    # ========================================================

    def process_frame(
        self,
        frame,
        execute_action: bool = True,
        draw_landmarks: bool = True,
    ):
        """
        Process one webcam frame.

        This method DOES NOT open the camera.

        Parameters
        ----------
        frame:
            OpenCV BGR frame.

        execute_action:
            If True, CursorController executes the gesture.

        draw_landmarks:
            If True, hand landmarks are drawn on the frame.

        Returns
        -------
        dict
            Runtime information for the dashboard.
        """

        if frame is None:

            return {
                "frame": frame,
                "gesture": "None",
                "action": "None",
                "hand": "None",
                "detected": False,
            }

        # ----------------------------------------------------
        # MIRROR FRAME
        # ----------------------------------------------------

        frame = cv2.flip(
            frame,
            1,
        )

        # ----------------------------------------------------
        # HAND DETECTION
        # ----------------------------------------------------

        results, detected_hands = (
            self.detector.process(frame)
        )

        self.last_results = results
        self.last_detected_hands = detected_hands

        # ----------------------------------------------------
        # DRAW LANDMARKS
        # ----------------------------------------------------

        if draw_landmarks:

            self.detector.draw_landmarks(
                frame,
                results,
            )

        # ----------------------------------------------------
        # FIND PRIMARY HAND
        # ----------------------------------------------------

        hand = self.detector.get_primary_hand(
            detected_hands,
            preferred_label=self.preferred_hand,
        )

        # ----------------------------------------------------
        # NO HAND
        # ----------------------------------------------------

        if hand is None:

            self.classifier.reset()

            self.controller.reset()

            gesture = Gesture.NONE

            self.current_gesture = gesture
            self.current_hand = "None"
            self.current_action = "None"

            self._draw_dashboard_status(
                frame,
                gesture,
                None,
            )

            return {
                "frame": frame,
                "gesture": "None",
                "action": "None",
                "hand": "None",
                "detected": False,
            }

        # ----------------------------------------------------
        # CLASSIFY GESTURE
        # ----------------------------------------------------

        gesture = self.classifier.classify(
            hand.landmarks
        )

        self.current_gesture = gesture

        self.current_hand = (
            getattr(
                hand,
                "label",
                "Unknown",
            )
        )

        # ----------------------------------------------------
        # EXECUTE ACTION
        # ----------------------------------------------------

        if execute_action:

            self.controller.handle_gesture(
                gesture,
                hand.landmarks,
            )

        # ----------------------------------------------------
        # ACTION NAME
        # ----------------------------------------------------

        action = self._gesture_to_action(
            gesture
        )

        self.current_action = action

        # ----------------------------------------------------
        # DRAW DASHBOARD STATUS
        # ----------------------------------------------------

        self._draw_dashboard_status(
            frame,
            gesture,
            hand,
        )

        return {
            "frame": frame,
            "gesture": self._gesture_name(
                gesture
            ),
            "action": action,
            "hand": self.current_hand,
            "detected": True,
        }

    # ========================================================
    # GESTURE NAME
    # ========================================================

    @staticmethod
    def _gesture_name(
        gesture,
    ):

        try:

            if hasattr(
                gesture,
                "value",
            ):

                return str(
                    gesture.value
                ).replace(
                    "_",
                    " ",
                ).title()

            return str(
                gesture
            )

        except Exception:

            return "Unknown"

    # ========================================================
    # GESTURE → ACTION
    # ========================================================

    @staticmethod
    def _gesture_to_action(
        gesture,
    ):

        """
        Human-readable action name.

        This is only for dashboard display.
        Actual action execution remains inside
        CursorController.
        """

        name = (
            HandGestureMouse._gesture_name(
                gesture
            )
            .lower()
        )

        # ----------------------------------------------------
        # Known gesture names
        # ----------------------------------------------------

        mapping = {

            "none":
                "Neutral",

            "fist":
                "Drag / Hold",

            "pinky":
                "Scroll Down",

            "ring":
                "Ring Gesture",

            "mid":
                "Left Click",

            "last3":
                "Scroll",

            "index":
                "Right Click",

            "first2":
                "Cursor / Two Finger",

            "last4":
                "Gesture Control",

            "thumb":
                "Scroll Up",

            "palm":
                "Neutral",

            "v gest":
                "Cursor Movement",

            "two finger closed":
                "Double Click",

            "pinch major":
                "System Control",

            "pinch minor":
                "Scroll Control",
        }

        return mapping.get(
            name,
            "Gesture Detected",
        )

    # ========================================================
    # DASHBOARD STATUS DRAWING
    # ========================================================

    def _draw_dashboard_status(
        self,
        frame,
        gesture,
        hand,
    ):
        """
        Draw status directly onto the supplied frame.

        This is useful for the Streamlit camera preview.
        """

        gesture_name = (
            self._gesture_name(
                gesture
            )
            .upper()
        )

        if hand is None:

            hand_text = "NO HAND"

        else:

            hand_text = (
                f"{getattr(hand, 'label', 'UNKNOWN')} HAND"
            )

        # ----------------------------------------------------
        # STATUS BACKGROUND
        # ----------------------------------------------------

        cv2.rectangle(
            frame,
            (10, 10),
            (470, 105),
            (20, 20, 20),
            -1,
        )

        # ----------------------------------------------------
        # HAND
        # ----------------------------------------------------

        cv2.putText(
            frame,
            f"Hand: {hand_text}",
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2,
        )

        # ----------------------------------------------------
        # GESTURE
        # ----------------------------------------------------

        cv2.putText(
            frame,
            f"Gesture: {gesture_name}",
            (20, 65),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2,
        )

        # ----------------------------------------------------
        # ACTION
        # ----------------------------------------------------

        cv2.putText(
            frame,
            f"Action: {self.current_action}",
            (20, 92),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            1,
        )

    # ========================================================
    # START STANDALONE MODE
    # ========================================================

    def start(self) -> None:
        """
        Existing standalone mode.

        This method still owns the webcam and opens
        the normal OpenCV window.

        The dashboard will NOT use this method.
        """

        self.cap = cv2.VideoCapture(
            self.camera_index
        )

        if not self.cap.isOpened():

            raise RuntimeError(
                f"Unable to open camera "
                f"{self.camera_index}."
            )

        # ----------------------------------------------------
        # CAMERA RESOLUTION
        # ----------------------------------------------------

        self.cap.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            640,
        )

        self.cap.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            480,
        )

        # ----------------------------------------------------
        # REDUCE CAMERA BUFFER
        # ----------------------------------------------------

        self.cap.set(
            cv2.CAP_PROP_BUFFERSIZE,
            1,
        )

        self.running = True

        try:

            while self.running:

                success, frame = (
                    self.cap.read()
                )

                if not success:

                    print(
                        "Unable to read camera frame."
                    )

                    continue

                result = self.process_frame(
                    frame,
                    execute_action=True,
                    draw_landmarks=True,
                )

                display_frame = result[
                    "frame"
                ]

                if self.show_window:

                    cv2.imshow(
                        self.WINDOW_NAME,
                        display_frame,
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

    # ========================================================
    # STOP
    # ========================================================

    def stop(self) -> None:
        """
        Safely stop the standalone controller.

        Dashboard mode does not call this to release
        the dashboard camera; the dashboard owns that camera.
        """

        self.running = False

        # Release any standalone camera
        if self.cap is not None:

            self.cap.release()

            self.cap = None

        # Reset cursor state
        try:

            self.controller.reset()

        except Exception:

            pass

        # Close detector
        try:

            self.detector.close()

        except Exception:

            pass

        # Close OpenCV windows
        try:

            cv2.destroyAllWindows()

        except Exception:

            pass

    # ========================================================
    # DASHBOARD RESET
    # ========================================================

    def reset_processing_state(self):
        """
        Reset gesture processing without releasing
        the detector.

        Used when dashboard changes mode.
        """

        try:

            self.classifier.reset()

        except Exception:

            pass

        try:

            self.controller.reset()

        except Exception:

            pass

        self.current_gesture = (
            Gesture.NONE
        )

        self.current_action = "None"
        self.current_hand = "None"


# ============================================================
# STANDALONE ENTRY POINT
# ============================================================

def run_hand_gesture():

    app = HandGestureMouse()

    app.start()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    run_hand_gesture()