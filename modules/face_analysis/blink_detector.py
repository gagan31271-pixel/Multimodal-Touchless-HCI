# ============================================================
# BLINK / WINK DETECTOR
# ============================================================

import math
import time

import pyautogui

from config import (
    EYE_CLOSED_THRESHOLD,
    WINK_STABLE_FRAMES,
    WINK_COOLDOWN,
    ENABLE_EYE_CLICKS,
)


class BlinkDetector:

    # --------------------------------------------------------
    # MediaPipe Face Mesh eye landmarks
    #
    # LEFT EYE:
    # 33, 160, 158, 133, 153, 144
    #
    # RIGHT EYE:
    # 362, 385, 387, 263, 373, 380
    # --------------------------------------------------------

    LEFT_EYE = [
        33,
        160,
        158,
        133,
        153,
        144,
    ]

    RIGHT_EYE = [
        362,
        385,
        387,
        263,
        373,
        380,
    ]

    def __init__(self):

        # ----------------------------------------------------
        # Eye state
        # ----------------------------------------------------

        self.left_closed_frames = 0

        self.right_closed_frames = 0

        # ----------------------------------------------------
        # Click cooldown
        # ----------------------------------------------------

        self.last_click_time = 0.0

        # ----------------------------------------------------
        # Current action
        # ----------------------------------------------------

        self.last_action = "None"

    # ========================================================
    # DISTANCE
    # ========================================================

    @staticmethod
    def distance(a, b):

        return math.sqrt(
            (a.x - b.x) ** 2
            +
            (a.y - b.y) ** 2
        )

    # ========================================================
    # EYE ASPECT RATIO
    # ========================================================

    def calculate_ear(
        self,
        landmarks,
        indices
    ):

        p1 = landmarks[indices[0]]
        p2 = landmarks[indices[1]]
        p3 = landmarks[indices[2]]
        p4 = landmarks[indices[3]]
        p5 = landmarks[indices[4]]
        p6 = landmarks[indices[5]]

        vertical_1 = self.distance(
            p2,
            p6
        )

        vertical_2 = self.distance(
            p3,
            p5
        )

        horizontal = self.distance(
            p1,
            p4
        )

        if horizontal == 0:

            return 0.0

        return (
            vertical_1
            +
            vertical_2
        ) / (
            2.0 * horizontal
        )

    # ========================================================
    # GET EYE STATES
    # ========================================================

    def get_eye_states(
        self,
        landmarks
    ):

        left_ear = self.calculate_ear(
            landmarks,
            self.LEFT_EYE
        )

        right_ear = self.calculate_ear(
            landmarks,
            self.RIGHT_EYE
        )

        left_closed = (
            left_ear
            < EYE_CLOSED_THRESHOLD
        )

        right_closed = (
            right_ear
            < EYE_CLOSED_THRESHOLD
        )

        return (
            left_ear,
            right_ear,
            left_closed,
            right_closed
        )

    # ========================================================
    # DETECT WINK
    # ========================================================

    def detect_wink(
        self,
        landmarks
    ):

        (
            left_ear,
            right_ear,
            left_closed,
            right_closed
        ) = self.get_eye_states(
            landmarks
        )

        # ----------------------------------------------------
        # Update frame counters
        # ----------------------------------------------------

        if left_closed:

            self.left_closed_frames += 1

        else:

            self.left_closed_frames = 0


        if right_closed:

            self.right_closed_frames += 1

        else:

            self.right_closed_frames = 0

        current_time = time.time()

        action = "None"

        # ====================================================
        # LEFT EYE WINK
        #
        # LEFT BLINK -> LEFT CLICK
        # ====================================================

        if (
            self.left_closed_frames
            >= WINK_STABLE_FRAMES
            and
            not right_closed
        ):

            if (
                current_time
                - self.last_click_time
                >= WINK_COOLDOWN
            ):

                if ENABLE_EYE_CLICKS:

                    pyautogui.click()

                self.last_click_time = (
                    current_time
                )

                action = "Left Click"

                self.left_closed_frames = 0

        # ====================================================
        # RIGHT EYE WINK
        #
        # RIGHT BLINK -> RIGHT CLICK
        # ====================================================

        elif (
            self.right_closed_frames
            >= WINK_STABLE_FRAMES
            and
            not left_closed
        ):

            if (
                current_time
                - self.last_click_time
                >= WINK_COOLDOWN
            ):

                if ENABLE_EYE_CLICKS:

                    pyautogui.rightClick()

                self.last_click_time = (
                    current_time
                )

                action = "Right Click"

                self.right_closed_frames = 0

        # ====================================================
        # NORMAL BLINK
        #
        # Both eyes closed -> no click
        # ====================================================

        elif (
            left_closed
            and right_closed
        ):

            action = "Blink"

        self.last_action = action

        return {
            "left_ear": left_ear,
            "right_ear": right_ear,
            "left_closed": left_closed,
            "right_closed": right_closed,
            "action": action,
        }

    # ========================================================
    # RESET
    # ========================================================

    def reset(self):

        self.left_closed_frames = 0

        self.right_closed_frames = 0

        self.last_action = "None"