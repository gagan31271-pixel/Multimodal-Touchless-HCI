# ============================================================
# FACE DETECTOR
# MediaPipe Face Mesh
# ============================================================

import cv2
import mediapipe as mp


class FaceDetector:

    # --------------------------------------------------------
    # Important facial landmark groups used only for display
    # --------------------------------------------------------

    # Eye landmarks used by BlinkDetector
    LEFT_EYE_POINTS = [
        33,
        160,
        158,
        133,
        153,
        144,
    ]

    RIGHT_EYE_POINTS = [
        362,
        385,
        387,
        263,
        373,
        380,
    ]

    # Small number of nose landmarks
    NOSE_POINTS = [
        1,
        2,
        4,
        5,
        275,
    ]

    # Small number of mouth landmarks
    MOUTH_POINTS = [
        61,
        291,
        13,
        14,
    ]

    # A few eyebrow points
    EYEBROW_POINTS = [
        70,
        107,
        336,
        300,
    ]

    def __init__(self):

        self.mp_face_mesh = (
            mp.solutions.face_mesh
        )

        self.face_mesh = (
            self.mp_face_mesh.FaceMesh(

                static_image_mode=False,

                max_num_faces=1,

                refine_landmarks=True,

                min_detection_confidence=0.6,

                min_tracking_confidence=0.6,
            )
        )

    # ========================================================
    # PROCESS FRAME
    # ========================================================

    def process(self, frame):

        # OpenCV BGR -> MediaPipe RGB

        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        rgb.flags.writeable = False

        results = (
            self.face_mesh.process(
                rgb
            )
        )

        rgb.flags.writeable = True

        return results

    # ========================================================
    # DRAW SELECTIVE LANDMARKS
    #
    # Instead of drawing all 468 points,
    # only important eye/nose/mouth points are shown.
    # ========================================================

    def draw_landmarks(
        self,
        frame,
        results
    ):

        if not results.multi_face_landmarks:

            return

        for face_landmarks in (
            results.multi_face_landmarks
        ):

            landmarks = (
                face_landmarks.landmark
            )

            # ------------------------------------------------
            # Combine only selected points
            # ------------------------------------------------

            selected_points = (
                self.LEFT_EYE_POINTS
                + self.RIGHT_EYE_POINTS
                + self.NOSE_POINTS
                + self.MOUTH_POINTS
                + self.EYEBROW_POINTS
            )

            # ------------------------------------------------
            # Draw small points
            # ------------------------------------------------

            for index in selected_points:

                point = landmarks[index]

                x = int(
                    point.x * frame.shape[1]
                )

                y = int(
                    point.y * frame.shape[0]
                )

                # Small dot instead of large mesh.

                cv2.circle(
                    frame,
                    (x, y),
                    2,
                    (0, 255, 255),
                    -1
                )

    # ========================================================
    # CLOSE
    # ========================================================

    def close(self):

        self.face_mesh.close()