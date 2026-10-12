from __future__ import annotations

import threading
import time
from enum import Enum
from typing import Optional


class InteractionMode(str, Enum):
    NONE = "none"
    HAND = "hand"
    EYE = "eye"
    VOICE = "voice"


class ModeManager:
    """
    Central controller for the Touchless HCI interaction modes.

    Only ONE primary interaction mode is active at a time.

    HAND  -> Hand Gesture Mouse
    EYE   -> Eye/Wink interaction
    VOICE -> MAX Voice Assistant

    OCR/AI is intentionally kept outside this manager because it is
    a shared service for all interaction modes.
    """

    def __init__(self) -> None:

        self.current_mode = InteractionMode.NONE

        self.hand_controller = None
        self.hand_thread: Optional[threading.Thread] = None

        self.max_assistant = None
        self.max_thread: Optional[threading.Thread] = None

        self.running = True

    # ============================================================
    # STATUS
    # ============================================================

    def show_status(self) -> None:

        print()
        print("=" * 65)
        print("MULTIMODAL TOUCHLESS HCI - MODE MANAGER")
        print("=" * 65)

        print(
            f"Current mode: {self.current_mode.value.upper()}"
        )

        print()
        print("1. Hand Gesture Mode")
        print("2. Eye / Wink Mode")
        print("3. Voice / MAX Mode")
        print("0. Exit")

        print("=" * 65)

    # ============================================================
    # STOP CURRENT MODE
    # ============================================================

    def stop_current_mode(self) -> None:

        if self.current_mode == InteractionMode.HAND:

            self.stop_hand_mode()

        elif self.current_mode == InteractionMode.VOICE:

            self.stop_voice_mode()

        elif self.current_mode == InteractionMode.EYE:

            self.stop_eye_mode()

        self.current_mode = InteractionMode.NONE

    # ============================================================
    # HAND MODE
    # ============================================================

    def start_hand_mode(self) -> None:

        if self.current_mode == InteractionMode.HAND:

            print("[MODE] Hand mode is already active.")
            return

        self.stop_current_mode()

        try:

            from modules.hand_gesture.hand_mouse import (
                HandGestureMouse,
            )

            controller = HandGestureMouse(
                camera_index=0,
                preferred_hand="Right",
                show_window=True,
            )

            self.hand_controller = controller

            def run_hand() -> None:

                try:

                    controller.start()

                except Exception as exc:

                    print(
                        f"[HAND] Error: {exc}"
                    )

            self.hand_thread = threading.Thread(
                target=run_hand,
                daemon=True,
            )

            self.hand_thread.start()

            time.sleep(0.8)

            if (
                self.hand_thread.is_alive()
            ):

                self.current_mode = (
                    InteractionMode.HAND
                )

                print(
                    "[MODE] Hand Gesture Mode ACTIVE."
                )

            else:

                self.hand_controller = None
                self.hand_thread = None

        except Exception as exc:

            print(
                f"[MODE] Could not start Hand Mode: {exc}"
            )

    def stop_hand_mode(self) -> None:

        if self.hand_controller is None:
            return

        print(
            "[MODE] Stopping Hand Gesture Mode..."
        )

        try:

            self.hand_controller.stop()

        except Exception as exc:

            print(
                f"[HAND] Stop error: {exc}"
            )

        if (
            self.hand_thread is not None
            and self.hand_thread.is_alive()
        ):

            self.hand_thread.join(
                timeout=1.5
            )

        self.hand_controller = None
        self.hand_thread = None

        print(
            "[MODE] Hand Gesture Mode STOPPED."
        )

    # ============================================================
    # EYE MODE
    # ============================================================

        def start_eye_mode(self) -> None:

            if self.current_mode == InteractionMode.EYE:

                print(
                    "[MODE] Eye/Wink Mode is already active."
                )
                return

            self.stop_current_mode()

            try:

                from modules.multimodal.eye_mode import (
                    EyeMode,
                )

                controller = EyeMode(
                    camera_index=0
                )

                self.eye_controller = controller

                def run_eye() -> None:

                    try:

                        controller.start()

                    except Exception as exc:

                        print(
                            f"[EYE] Error: {exc}"
                        )

                self.eye_thread = threading.Thread(
                    target=run_eye,
                    daemon=True,
                )

                self.eye_thread.start()

                time.sleep(0.8)

                if self.eye_thread.is_alive():

                    self.current_mode = (
                        InteractionMode.EYE
                    )

                    print(
                        "[MODE] Eye/Wink Mode ACTIVE."
                    )

                else:

                    self.eye_controller = None
                    self.eye_thread = None

            except Exception as exc:

                print(
                    f"[MODE] Could not start Eye Mode: {exc}"
                )

        def stop_eye_mode(self) -> None:

            if getattr(
                self,
                "eye_controller",
                None,
            ) is None:

                return

            print(
                "[MODE] Stopping Eye/Wink Mode..."
            )

            try:

                self.eye_controller.stop()

            except Exception as exc:

                print(
                    f"[EYE] Stop error: {exc}"
                )

            if (
                getattr(self, "eye_thread", None)
                is not None
                and self.eye_thread.is_alive()
            ):

                self.eye_thread.join(
                    timeout=1.5
                )

            self.eye_controller = None
            self.eye_thread = None

            print(
                "[MODE] Eye/Wink Mode STOPPED."
            )
    # ============================================================
    # VOICE / MAX MODE
    # ============================================================

    def start_voice_mode(self) -> None:

        if self.current_mode == InteractionMode.VOICE:

            print(
                "[MODE] Voice/MAX Mode is already active."
            )
            return

        self.stop_current_mode()

        try:

            from modules.voice_command.max import MAX

            assistant = MAX()

            self.max_assistant = assistant

            def run_max() -> None:

                try:

                    assistant.run()

                except Exception as exc:

                    print(
                        f"[MAX] Error: {exc}"
                    )

            self.max_thread = threading.Thread(
                target=run_max,
                daemon=True,
            )

            self.max_thread.start()

            time.sleep(1.0)

            if (
                self.max_thread.is_alive()
            ):

                self.current_mode = (
                    InteractionMode.VOICE
                )

                print(
                    "[MODE] Voice/MAX Mode ACTIVE."
                )

            else:

                self.max_assistant = None
                self.max_thread = None

        except Exception as exc:

            print(
                f"[MODE] Could not start Voice Mode: {exc}"
            )

    def stop_voice_mode(self) -> None:

        if self.max_assistant is None:
            return

        print(
            "[MODE] Stopping Voice/MAX Mode..."
        )

        try:

            self.max_assistant.shutdown()

        except Exception as exc:

            print(
                f"[MAX] Shutdown error: {exc}"
            )

        if (
            self.max_thread is not None
            and self.max_thread.is_alive()
        ):

            self.max_thread.join(
                timeout=2.0
            )

        self.max_assistant = None
        self.max_thread = None

        print(
            "[MODE] Voice/MAX Mode STOPPED."
        )

    # ============================================================
    # MODE SELECTION
    # ============================================================

    def select_mode(
        self,
        choice: str,
    ) -> None:

        choice = choice.strip()

        if choice == "1":

            self.start_hand_mode()

        elif choice == "2":

            self.start_eye_mode()

        elif choice == "3":

            self.start_voice_mode()

        elif choice == "0":

            self.running = False

            self.stop_current_mode()

        else:

            print(
                "[MODE] Invalid option."
            )

    # ============================================================
    # MAIN LOOP
    # ============================================================

    def run(self) -> None:

        print()
        print(
            "Starting Multimodal Touchless HCI..."
        )

        while self.running:

            self.show_status()

            try:

                choice = input(
                    "Select mode: "
                )

            except KeyboardInterrupt:

                print()

                self.running = False

                break

            self.select_mode(
                choice
            )

        self.shutdown()

    # ============================================================
    # SHUTDOWN
    # ============================================================

    def shutdown(self) -> None:

        print()
        print(
            "[MODE] Shutting down all modes..."
        )

        self.stop_current_mode()

        self.current_mode = (
            InteractionMode.NONE
        )

        print(
            "[MODE] Multimodal HCI Mode Manager stopped."
        )


def main() -> None:

    manager = ModeManager()

    try:

        manager.run()

    except KeyboardInterrupt:

        print()

    finally:

        manager.shutdown()


if __name__ == "__main__":
    main()