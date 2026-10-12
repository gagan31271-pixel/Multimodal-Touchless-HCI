"""
Robust MediaPipe Hand Detector
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import cv2
import mediapipe as mp


@dataclass
class DetectedHand:
    landmarks: object
    label: str
    confidence: float


class HandDetector:

    def __init__(
        self,
        max_num_hands: int = 2,
        min_detection_confidence: float = 0.45,
        min_tracking_confidence: float = 0.45,
    ) -> None:

        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils

        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,

            # Allows recovery when tracking is temporarily lost.
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,

            # Better landmark quality than the lightweight model.
            model_complexity=0,
        )

    def process(self, frame):

        if frame is None:
            return None, []

        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB,
        )

        rgb.flags.writeable = False

        results = self.hands.process(rgb)

        detected_hands = []

        if not results.multi_hand_landmarks:
            return results, detected_hands

        handedness_list = (
            results.multi_handedness or []
        )

        for i, landmarks in enumerate(
            results.multi_hand_landmarks
        ):

            label = "Unknown"
            confidence = 0.0

            if i < len(handedness_list):

                classification = (
                    handedness_list[i]
                    .classification[0]
                )

                label = classification.label
                confidence = float(
                    classification.score
                )

            detected_hands.append(
                DetectedHand(
                    landmarks=landmarks,
                    label=label,
                    confidence=confidence,
                )
            )

        return results, detected_hands

    @staticmethod
    def get_primary_hand(
        detected_hands: list[DetectedHand],
        preferred_label: str = "Right",
    ) -> Optional[DetectedHand]:

        if not detected_hands:
            return None

        # Prefer the selected hand.
        for hand in detected_hands:

            if hand.label == preferred_label:
                return hand

        # Otherwise select the highest-confidence hand.
        return max(
            detected_hands,
            key=lambda hand: hand.confidence,
        )

    def draw_landmarks(
        self,
        frame,
        results,
    ) -> None:

        if (
            results is None
            or not results.multi_hand_landmarks
        ):
            return

        for hand_landmarks in (
            results.multi_hand_landmarks
        ):

            self.mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                self.mp_hands.HAND_CONNECTIONS,
            )

    def close(self) -> None:

        self.hands.close()