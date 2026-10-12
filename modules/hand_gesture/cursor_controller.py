"""
Cursor Controller
-----------------
Converts hand gestures into mouse actions.
"""

from __future__ import annotations

import time

import pyautogui

from .gesture_classifier import Gesture
from .smoothing import PointSmoother


class CursorController:
    """Controls the mouse using hand gestures."""

    def __init__(
        self,
        smoothing_alpha: float = 0.35,
        click_cooldown: float = 0.45,
        scroll_cooldown: float = 0.25,
        scroll_up_speed: int = 6,
        scroll_down_speed: int = 4,
    ) -> None:

        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.01

        self.screen_width, self.screen_height = pyautogui.size()

        self.smoother = PointSmoother(
            alpha=0.32
        )

        self.cursor_speed = 0.85

        self.click_cooldown = click_cooldown
        self.scroll_cooldown = scroll_cooldown

        self.scroll_up_speed = 8
        self.scroll_down_speed = 6

        self.last_click_time = 0.0
        self.last_scroll_time = 0.0

        self.dragging = False
        self.previous_gesture = Gesture.NONE

    def _clamp(
        self,
        value: float,
        minimum: float,
        maximum: float,
    ) -> float:

        return max(
            minimum,
            min(value, maximum),
        )

    def move_from_landmark(self, landmark) -> None:
        """Move cursor using normalized hand coordinates."""

        x = landmark.x * self.screen_width
        y = landmark.y * self.screen_height

        # Target position.
        target_x = self._clamp(
            x,
            0,
            self.screen_width - 1,
        )

        target_y = self._clamp(
            y,
            0,
            self.screen_height - 1,
        )

        # Smooth the target.
        smooth_x, smooth_y = self.smoother.update(
            target_x,
            target_y,
        )

        # Slow cursor movement slightly by moving only part
        # of the distance from the current position.
        current_x, current_y = pyautogui.position()

        new_x = current_x + (
            smooth_x - current_x
        ) * self.cursor_speed

        new_y = current_y + (
            smooth_y - current_y
        ) * self.cursor_speed

        new_x = self._clamp(
            new_x,
            0,
            self.screen_width - 1,
        )

        new_y = self._clamp(
            new_y,
            0,
            self.screen_height - 1,
        )

        pyautogui.moveTo(
            int(new_x),
            int(new_y),
            duration=0,
        )
    def left_click(self) -> None:
        """Perform a left click."""

        now = time.monotonic()

        if (
            now - self.last_click_time
            < self.click_cooldown
        ):
            return

        pyautogui.click(button="left")

        self.last_click_time = now

    def right_click(self) -> None:
        """Perform a right click."""

        now = time.monotonic()

        if (
            now - self.last_click_time
            < self.click_cooldown
        ):
            return

        pyautogui.click(button="right")

        self.last_click_time = now

    def start_drag(self) -> None:
        """Start mouse drag."""

        if self.dragging:
            return

        pyautogui.mouseDown(button="left")
        self.dragging = True

    def stop_drag(self) -> None:
        """Stop mouse drag."""

        if not self.dragging:
            return

        pyautogui.mouseUp(button="left")
        self.dragging = False

    def scroll_up(self) -> None:
        """Scroll upward."""

        now = time.monotonic()

        if (
            now - self.last_scroll_time
            < self.scroll_cooldown
        ):
            return

        pyautogui.scroll(
            self.scroll_up_speed
        )

        self.last_scroll_time = now

    def scroll_down(self) -> None:
        """Scroll downward."""

        now = time.monotonic()

        if (
            now - self.last_scroll_time
            < self.scroll_cooldown
        ):
            return

        pyautogui.scroll(
            -self.scroll_down_speed
        )

        self.last_scroll_time = now

    def handle_gesture(
        self,
        gesture: Gesture,
        hand_result,
    ) -> None:
        """Execute the action associated with a gesture."""

        if gesture is None:
            gesture = Gesture.NONE

        # Leave drag mode when gesture changes.
        if gesture != Gesture.INDEX_LITTLE:
            self.stop_drag()

        # -----------------------------------------------------
        # INDEX ONLY -> CURSOR
        # -----------------------------------------------------

        if gesture == Gesture.INDEX_ONLY:

            if hand_result is not None:
                self.move_from_landmark(
                    hand_result.landmark[8]
                )

        # -----------------------------------------------------
        # TWO FINGER -> LEFT CLICK
        # -----------------------------------------------------

        elif gesture == Gesture.TWO_FINGER:

            self.left_click()

        # -----------------------------------------------------
        # THREE FINGER -> RIGHT CLICK
        # -----------------------------------------------------

        elif gesture == Gesture.THREE_FINGER:

            self.right_click()

        # -----------------------------------------------------
        # INDEX + LITTLE -> DRAG
        # -----------------------------------------------------

        elif gesture == Gesture.INDEX_LITTLE:

            if hand_result is not None:
                self.move_from_landmark(
                    hand_result.landmark[8]
                )

            self.start_drag()

        # -----------------------------------------------------
        # THUMB ONLY -> SCROLL UP
        # -----------------------------------------------------

        elif gesture == Gesture.THUMB_UP:

            self.scroll_up()

        # -----------------------------------------------------
        # THUMB + LITTLE -> SCROLL DOWN
        # -----------------------------------------------------

        elif gesture == Gesture.THUMB_LITTLE:

            self.scroll_down()

        # -----------------------------------------------------
        # FIST / NONE
        # -----------------------------------------------------

        elif gesture in (
            Gesture.FIST,
            Gesture.NONE,
        ):

            self.stop_drag()

        self.previous_gesture = gesture

    def reset(self) -> None:
        """Return controller to safe state."""

        self.stop_drag()
        self.smoother.reset()
        self.previous_gesture = Gesture.NONE