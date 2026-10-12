# ============================================================
# BLINK / WINK TEST PROGRAM
# ============================================================
import os
import sys

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
    SHOW_EYE_CAMERA,
    SHOW_EYE_LANDMARKS,
)

from modules.face_detector import FaceDetector
from modules.blink_detector import BlinkDetector


def main():

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

    face_detector = FaceDetector()

    blink_detector = BlinkDetector()

    print()

    print("=" * 65)

    print(
        "          EYE BLINK / WINK TEST"
    )

    print("=" * 65)

    print()

    print(
        "Right-eye wink -> Left click"
    )

    print(
        "Left-eye wink  -> Right click"
    )

    print(
        "Normal blink    -> No action"
    )

    print()

    print(
        "Press Q or ESC to exit."
    )

    print("=" * 65)

    try:

        while True:

            success, frame = (
                camera.read()
            )

            if not success:

                continue

            # Mirror camera.

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

            action = "No Face"

            left_ear = 0.0

            right_ear = 0.0

            if (
                results.multi_face_landmarks
            ):

                face_landmarks = (
                    results
                    .multi_face_landmarks[0]
                )

                landmarks = (
                    face_landmarks.landmark
                )

                # Blink detection.

                data = (
                    blink_detector.detect_wink(
                        landmarks
                    )
                )

                left_ear = data[
                    "left_ear"
                ]

                right_ear = data[
                    "right_ear"
                ]

                action = data[
                    "action"
                ]

                # Draw landmarks.

                if SHOW_EYE_LANDMARKS:

                    face_detector.draw_landmarks(
                        frame,
                        results
                    )

            # ------------------------------------------------
            # Information panel
            # ------------------------------------------------

            cv2.rectangle(
                frame,
                (10, 10),
                (430, 160),
                (0, 0, 0),
                -1
            )

            cv2.putText(
                frame,
                f"Left EAR: {left_ear:.3f}",
                (25, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2
            )

            cv2.putText(
                frame,
                f"Right EAR: {right_ear:.3f}",
                (25, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2
            )

            cv2.putText(
                frame,
                f"Action: {action}",
                (25, 105),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.70,
                (0, 255, 0),
                2
            )

            cv2.putText(
                frame,
                "Q / ESC = Exit",
                (25, 138),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                1
            )

            # ------------------------------------------------
            # Display
            # ------------------------------------------------

            if SHOW_EYE_CAMERA:

                cv2.imshow(
                    "Touchless HCI - Eye Control",
                    frame
                )

            # ------------------------------------------------
            # Exit
            # ------------------------------------------------

            key = (
                cv2.waitKey(1)
                & 0xFF
            )

            if (
                key == ord("q")
                or key == ord("Q")
                or key == 27
            ):

                break

    except KeyboardInterrupt:

        print(
            "\nStopping eye test..."
        )

    finally:

        camera.release()

        cv2.destroyAllWindows()

        face_detector.close()

        print(
            "Eye blink test stopped."
        )


if __name__ == "__main__":

    main()