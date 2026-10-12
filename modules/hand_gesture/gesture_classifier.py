"""
Robust Hand Gesture Classifier
==============================

Multimodal Touchless HCI

Gesture mapping:

INDEX_ONLY
    Index finger only -> cursor movement

TWO_FINGER
    Index + middle -> LEFT CLICK

THREE_FINGER
    Index + middle + ring -> RIGHT CLICK

INDEX_LITTLE
    Index + little -> DRAG

THUMB_UP
    Thumb only -> SCROLL UP

THUMB_LITTLE
    Thumb + little -> SCROLL DOWN

FIST
    No fingers -> NEUTRAL
"""

from __future__ import annotations

from enum import Enum
import math


class Gesture(str, Enum):

    NONE = "none"

    INDEX_ONLY = "index_only"

    TWO_FINGER = "two_finger"

    THREE_FINGER = "three_finger"

    INDEX_LITTLE = "index_little"

    THUMB_UP = "thumb_up"

    THUMB_LITTLE = "thumb_little"

    FIST = "fist"


class GestureClassifier:
    """
    Robust finger-state and gesture classifier.

    The finger-state logic is based on relative landmark geometry
    rather than strict joint-angle thresholds.
    """

    # ---------------------------------------------------------
    # MediaPipe landmark indexes
    # ---------------------------------------------------------

    WRIST = 0

    THUMB_CMC = 1
    THUMB_MCP = 2
    THUMB_IP = 3
    THUMB_TIP = 4

    INDEX_MCP = 5
    INDEX_PIP = 6
    INDEX_DIP = 7
    INDEX_TIP = 8

    MIDDLE_MCP = 9
    MIDDLE_PIP = 10
    MIDDLE_DIP = 11
    MIDDLE_TIP = 12

    RING_MCP = 13
    RING_PIP = 14
    RING_DIP = 15
    RING_TIP = 16

    LITTLE_MCP = 17
    LITTLE_PIP = 18
    LITTLE_DIP = 19
    LITTLE_TIP = 20

    def __init__(
        self,
        stable_frames: int = 3,
        release_frames: int = 2,
    ) -> None:

        self.stable_frames = stable_frames

        self.release_frames = release_frames

        self.previous_gesture = Gesture.NONE

        self.stable_gesture = Gesture.NONE

        self.frame_count = 0

        self.none_count = 0

    # =========================================================
    # BASIC GEOMETRY
    # =========================================================

    @staticmethod
    def _distance(a, b) -> float:

        dx = a.x - b.x

        dy = a.y - b.y

        return math.sqrt(
            dx * dx +
            dy * dy
        )

    @staticmethod
    def _signed_vertical_distance(
        landmarks,
        point_a: int,
        point_b: int,
    ) -> float:
        """
        Signed vertical distance between two landmarks.

        Positive:
            point_a is above point_b.

        Negative:
            point_a is below point_b.

        This follows the important idea used by the
        referenced gesture-control implementation.
        """

        sign = -1.0

        if (
            landmarks[point_a].y
            < landmarks[point_b].y
        ):
            sign = 1.0

        distance = GestureClassifier._distance(
            landmarks[point_a],
            landmarks[point_b],
        )

        return distance * sign

    # =========================================================
    # FINGER EXTENSION
    # =========================================================

    def _is_finger_extended(
        self,
        landmarks,
        tip: int,
        pip: int,
        mcp: int,
    ) -> bool:
        """
        Determine whether a finger is extended.

        Instead of requiring very specific joint angles,
        compare the relative position of the finger tip
        and the finger joints.

        This is considerably more tolerant to:
        - hand rotation
        - camera distance
        - partial bending
        - small landmark noise
        """

        upper = self._signed_vertical_distance(
            landmarks,
            tip,
            mcp,
        )

        lower = self._signed_vertical_distance(
            landmarks,
            pip,
            mcp,
        )

        if abs(lower) < 0.01:
            return False

        ratio = upper / abs(lower)

        return (
            ratio > 0.45
            and upper > 0
        )

    def _finger_states(
        self,
        landmarks,
    ) -> dict[str, bool]:
        """
        Calculate extension state of all fingers.
        """

        index = self._is_finger_extended(
            landmarks,
            self.INDEX_TIP,
            self.INDEX_PIP,
            self.INDEX_MCP,
        )

        middle = self._is_finger_extended(
            landmarks,
            self.MIDDLE_TIP,
            self.MIDDLE_PIP,
            self.MIDDLE_MCP,
        )

        ring = self._is_finger_extended(
            landmarks,
            self.RING_TIP,
            self.RING_PIP,
            self.RING_MCP,
        )

        little = self._is_finger_extended(
            landmarks,
            self.LITTLE_TIP,
            self.LITTLE_PIP,
            self.LITTLE_MCP,
        )

        thumb = self._is_thumb_extended(
            landmarks
        )

        return {
            "thumb": thumb,
            "index": index,
            "middle": middle,
            "ring": ring,
            "little": little,
        }

    # =========================================================
    # THUMB
    # =========================================================

    def _is_thumb_extended(
        self,
        landmarks,
    ) -> bool:
        """
        Thumb detection.

        The thumb behaves differently from the four other
        fingers, so it is evaluated separately.
        """

        thumb_tip = landmarks[self.THUMB_TIP]

        thumb_ip = landmarks[self.THUMB_IP]

        thumb_mcp = landmarks[self.THUMB_MCP]

        index_mcp = landmarks[self.INDEX_MCP]

        wrist = landmarks[self.WRIST]

        tip_from_mcp = self._distance(
            thumb_tip,
            thumb_mcp,
        )

        ip_from_mcp = self._distance(
            thumb_ip,
            thumb_mcp,
        )

        tip_from_wrist = self._distance(
            thumb_tip,
            wrist,
        )

        index_from_wrist = self._distance(
            index_mcp,
            wrist,
        )

        # Length test
        length_extended = (
            tip_from_mcp
            > ip_from_mcp * 1.10
        )

        # Thumb should extend away from the wrist.
        distance_extended = (
            tip_from_wrist
            > index_from_wrist * 0.75
        )

        return (
            length_extended
            and distance_extended
        )

    # =========================================================
    # RAW GESTURE
    # =========================================================

    def classify_raw(
        self,
        hand_result,
    ) -> Gesture:

        if hand_result is None:

            return Gesture.NONE

        landmarks = hand_result.landmark

        states = self._finger_states(
            landmarks
        )

        thumb = states["thumb"]

        index = states["index"]

        middle = states["middle"]

        ring = states["ring"]

        little = states["little"]

        # -----------------------------------------------------
        # RIGHT CLICK
        #
        # Index + middle + ring
        # -----------------------------------------------------

        if (
            index
            and middle
            and ring
            and not little
        ):
            return Gesture.THREE_FINGER

        # -----------------------------------------------------
        # LEFT CLICK
        #
        # Index + middle
        # -----------------------------------------------------

        if (
            index
            and middle
            and not ring
            and not little
        ):
            return Gesture.TWO_FINGER

        # -----------------------------------------------------
        # DRAG
        #
        # Index + little
        # -----------------------------------------------------

        if (
            index
            and little
            and not middle
            and not ring
        ):
            return Gesture.INDEX_LITTLE

        # -----------------------------------------------------
        # SCROLL DOWN
        #
        # Thumb + little
        # -----------------------------------------------------

        if (
            thumb
            and little
            and not index
            and not middle
            and not ring
        ):
            return Gesture.THUMB_LITTLE

        # -----------------------------------------------------
        # SCROLL UP
        #
        # Thumb only
        # -----------------------------------------------------

        if (
            thumb
            and not index
            and not middle
            and not ring
            and not little
        ):
            return Gesture.THUMB_UP

        # -----------------------------------------------------
        # CURSOR
        #
        # Index only
        # -----------------------------------------------------

        if (
            index
            and not middle
            and not ring
            and not little
        ):
            return Gesture.INDEX_ONLY

        # -----------------------------------------------------
        # FIST
        # -----------------------------------------------------

        if (
            not thumb
            and not index
            and not middle
            and not ring
            and not little
        ):
            return Gesture.FIST

        return Gesture.NONE

    # =========================================================
    # TEMPORAL STABILIZATION
    # =========================================================

    def classify(
        self,
        hand_result,
    ) -> Gesture:

        current = self.classify_raw(
            hand_result
        )

        # -----------------------------------------------------
        # Tracking temporarily uncertain
        # -----------------------------------------------------

        if current == Gesture.NONE:

            self.none_count += 1

            # Immediately release after a small number of
            # missing frames rather than staying stuck.
            if (
                self.none_count
                >= self.release_frames
            ):

                self.previous_gesture = Gesture.NONE

                self.stable_gesture = Gesture.NONE

                self.frame_count = 0

            return self.stable_gesture

        # We have a valid gesture.
        self.none_count = 0

        # -----------------------------------------------------
        # Same gesture continuing
        # -----------------------------------------------------

        if current == self.previous_gesture:

            self.frame_count += 1

        # -----------------------------------------------------
        # Gesture changed
        # -----------------------------------------------------

        else:

            self.previous_gesture = current

            self.frame_count = 1

        # -----------------------------------------------------
        # Accept gesture
        # -----------------------------------------------------

        if (
            self.frame_count
            >= self.stable_frames
        ):

            self.stable_gesture = current

        return self.stable_gesture

    # =========================================================
    # RESET
    # =========================================================

    def reset(self) -> None:

        self.previous_gesture = Gesture.NONE

        self.stable_gesture = Gesture.NONE

        self.frame_count = 0

        self.none_count = 0