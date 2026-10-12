# ============================================================
# FACIAL EXPRESSION TEST
# ============================================================

import os
import sys

# ------------------------------------------------------------
# Add project root to Python path
# ------------------------------------------------------------

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

sys.path.insert(
    0,
    PROJECT_ROOT
)

import cv2

from config import (
    CAMERA_INDEX,
    CAMERA_WIDTH,
    CAMERA_HEIGHT,
    CAMERA_FPS,
    SHOW_EXPRESSION_CAMERA,
    SHOW_EXPRESSION_LANDMARKS,
    EXPRESSION_CALIBRATION_FRAMES,
)

from modules.face_detector import FaceDetector
from modules.expression_detector import ExpressionDetector


def main():

    # ========================================================
    # CAMERA
    # ========================================================

    camera = cv2.VideoCapture(
        CAMERA_INDEX
    )

    camera.set(
        cv2.CAP_PROP_FRAME_WIDTH,
        CAMERA_WIDTH
    )

    camera.set(
        cv2.CAP_PROP_FRAME_HEIGHT,
        CAMERA_HEIGHT
    )

    camera.set(
        cv2.CAP_PROP_FPS,
        CAMERA_FPS
    )

    if not camera.isOpened():

        raise RuntimeError(
            "Could not open webcam."
        )

    # ========================================================
    # COMPONENTS
    # ========================================================

    face_detector = FaceDetector()

    expression_detector = ExpressionDetector()

    # ========================================================
    # TERMINAL INFORMATION
    # ========================================================

    print()

    print("=" * 70)

    print(
        "             FACIAL EXPRESSION TEST"
    )

    print("=" * 70)

    print()

    print(
        "Keep your face relaxed during calibration."
    )

    print(
        f"Calibration frames: "
        f"{EXPRESSION_CALIBRATION_FRAMES}"
    )

    print()

    print("Expressions to test:")

    print(
        "1. 🙂 Smile"
    )

    print(
        "2. 🤨 Eyebrow Raise"
    )

    print(
        "3. 😮 Mouth Open"
    )

    print(
        "4. 😠 Frown"
    )

    print(
        "5. 😲 Surprise"
    )

    print()

    print(
        "Press Q or ESC to exit."
    )

    print("=" * 70)

    # ========================================================
    # MAIN LOOP
    # ========================================================

    try:

        while True:

            # ------------------------------------------------
            # Capture frame
            # ------------------------------------------------

            success, frame = (
                camera.read()
            )

            if not success:

                continue

            # Mirror camera

            frame = cv2.flip(
                frame,
                1
            )

            # ------------------------------------------------
            # Face detection
            # ------------------------------------------------

            results = (
                face_detector.process(
                    frame
                )
            )

            # ------------------------------------------------
            # Default values
            # ------------------------------------------------

            expression = "No Face"

            smile_score = 0.0

            eyebrow_score = 0.0

            mouth_open_score = 0.0

            frown_score = 0.0

            eye_score = 0.0

            calibration_progress = 0.0

            # ------------------------------------------------
            # Face found
            # ------------------------------------------------

            if results.multi_face_landmarks:

                face_landmarks = (
                    results
                    .multi_face_landmarks[0]
                )

                landmarks = (
                    face_landmarks.landmark
                )

                # ------------------------------------------------
                # Expression detection
                # ------------------------------------------------

                data = (
                    expression_detector.detect(
                        landmarks
                    )
                )

                # ------------------------------------------------
                # Read results
                # ------------------------------------------------

                expression = data[
                    "expression"
                ]

                smile_score = data[
                    "smile_score"
                ]

                eyebrow_score = data[
                    "eyebrow_score"
                ]

                mouth_open_score = data[
                    "mouth_open_score"
                ]

                frown_score = data[
                    "frown_score"
                ]

                eye_score = data[
                    "eye_score"
                ]

                calibration_progress = data[
                    "calibration_progress"
                ]

                # ------------------------------------------------
                # Draw selected landmarks
                # ------------------------------------------------

                if SHOW_EXPRESSION_LANDMARKS:

                    face_detector.draw_landmarks(
                        frame,
                        results
                    )

            # ====================================================
            # STATUS PANEL
            # ====================================================

            cv2.rectangle(
                frame,
                (10, 10),
                (540, 275),
                (0, 0, 0),
                -1
            )

            # ------------------------------------------------
            # Expression
            # ------------------------------------------------

            cv2.putText(
                frame,
                f"Expression: {expression}",
                (25, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.70,
                (0, 255, 0),
                2
            )

            # ------------------------------------------------
            # Smile
            # ------------------------------------------------

            cv2.putText(
                frame,
                f"Smile: {smile_score:.3f}",
                (25, 72),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.50,
                (255, 255, 255),
                1
            )

            # ------------------------------------------------
            # Eyebrow
            # ------------------------------------------------

            cv2.putText(
                frame,
                f"Eyebrow: {eyebrow_score:.3f}",
                (25, 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.50,
                (255, 255, 255),
                1
            )

            # ------------------------------------------------
            # Mouth
            # ------------------------------------------------

            cv2.putText(
                frame,
                f"Mouth: {mouth_open_score:.3f}",
                (25, 128),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.50,
                (255, 255, 255),
                1
            )

            # ------------------------------------------------
            # Frown
            # ------------------------------------------------

            cv2.putText(
                frame,
                f"Frown: {frown_score:.3f}",
                (25, 156),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.50,
                (255, 255, 255),
                1
            )

            # ------------------------------------------------
            # Eye opening
            # ------------------------------------------------

            cv2.putText(
                frame,
                f"Eye: {eye_score:.3f}",
                (25, 184),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.50,
                (255, 255, 255),
                1
            )

            # ------------------------------------------------
            # Calibration
            # ------------------------------------------------

            if calibration_progress < 1.0:

                percent = (
                    calibration_progress
                    * 100
                )

                calibration_text = (
                    f"Calibration: {percent:.0f}%"
                )

            else:

                calibration_text = (
                    "Calibration: Complete"
                )

            cv2.putText(
                frame,
                calibration_text,
                (25, 215),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.50,
                (255, 255, 255),
                1
            )

            # ------------------------------------------------
            # Exit instruction
            # ------------------------------------------------

            cv2.putText(
                frame,
                "Q / ESC = Exit",
                (25, 245),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.50,
                (255, 255, 255),
                1
            )

            # ====================================================
            # DISPLAY
            # ====================================================

            if SHOW_EXPRESSION_CAMERA:

                cv2.imshow(
                    "Touchless HCI - Facial Expressions",
                    frame
                )

            # ====================================================
            # KEYBOARD
            # ====================================================

            key = (
                cv2.waitKey(1)
                &
                0xFF
            )

            if (
                key == ord("q")
                or
                key == ord("Q")
                or
                key == 27
            ):

                break

    # ========================================================
    # CTRL + C
    # ========================================================

    except KeyboardInterrupt:

        print(
            "\nStopping expression test..."
        )

    # ========================================================
    # CLEANUP
    # ========================================================

    finally:

        camera.release()

        cv2.destroyAllWindows()

        face_detector.close()

        print(
            "Facial expression test stopped."
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()