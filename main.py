"""
Multimodal Touchless Human-Computer Interaction Engine
=======================================================

Main application launcher.

Primary interaction modes:
    1. Hand Gesture Mode
    2. Eye / Wink Mode
    3. Voice / MAX Mode

Common services:
    - OCR screen reading
    - AI summarization
    - AI translation
    - TTS auditory feedback
    - Automatic application context switching

Only one primary interaction mode is active at a time.
"""

from __future__ import annotations

import traceback
from typing import Optional
from utils.telemetry import set_mode, reset
from modules.context_switcher.context_manager import ContextManager
from modules.multimodal.screen_service import ScreenService


# ============================================================
# MODE CREATION HELPERS
# ============================================================

def create_hand_mode():
    """Create the hand gesture controller."""
    from modules.hand_gesture.hand_mouse import HandGestureMouse

    return HandGestureMouse()


def create_eye_mode():
    """Create the eye/wink controller."""
    from modules.multimodal.eye_mode import EyeMode

    return EyeMode()


def create_voice_mode():
    """Create the MAX voice assistant."""
    from modules.voice_command.max import MAX

    return MAX()


# ============================================================
# MAIN APPLICATION
# ============================================================

class TouchlessHCI:
    """Main controller for the Multimodal Touchless HCI Engine."""

    def __init__(self) -> None:

        self.running = False

        # ----------------------------------------------------
        # Common services
        # ----------------------------------------------------

        print()
        print("[SYSTEM] Initializing common services...")

        self.screen_service: Optional[ScreenService] = None
        self.context_manager: Optional[ContextManager] = None

        # Screen service
        try:
            self.screen_service = ScreenService()

            print(
                "[SYSTEM] Screen Service initialized."
            )

        except Exception as exc:

            print(
                "[SYSTEM] Screen Service initialization failed: "
                f"{exc}"
            )

        # Context manager
        try:
            self.context_manager = ContextManager(
                check_interval=2.0,
                on_context_change=self._on_context_change,
            )

            print(
                "[SYSTEM] Context Manager initialized."
            )

        except Exception as exc:

            print(
                "[SYSTEM] Context Manager initialization failed: "
                f"{exc}"
            )

        # ----------------------------------------------------
        # Active primary interaction mode
        # ----------------------------------------------------

        self.active_mode_name: Optional[str] = None
        self.active_mode = None

    # ========================================================
    # CONTEXT CALLBACK
    # ========================================================

    def _on_context_change(
        self,
        context,
    ) -> None:
        """Called whenever the active application changes."""

        profile_name = context.get(
            "profile_name",
            "default",
        )

        application = context.get(
            "application",
            "Unknown",
        )

        print(
            "[SYSTEM] Context → "
            f"{profile_name.upper()} | "
            f"{application}"
        )

    # ========================================================
    # START BACKGROUND SERVICES
    # ========================================================

    def start_services(self) -> None:
        """Start background services."""

        if self.context_manager is not None:

            self.context_manager.start()

    # ========================================================
    # STOP ACTIVE MODE
    # ========================================================

    def stop_active_mode(self) -> None:
        """Safely stop the currently active mode."""

        if self.active_mode is None:

            self.active_mode_name = None
            return

        print()
        print(
            f"[SYSTEM] Stopping {self.active_mode_name}..."
        )

        try:

            if hasattr(
                self.active_mode,
                "stop",
            ):

                self.active_mode.stop()

            elif hasattr(
                self.active_mode,
                "shutdown",
            ):

                self.active_mode.shutdown()

        except Exception as exc:

            print(
                "[SYSTEM] Mode stop error: "
                f"{exc}"
            )

        finally:

            self.active_mode = None
            self.active_mode_name = None

    # ========================================================
    # HAND GESTURE MODE
    # ========================================================

    def run_hand_mode(self):
        print("\nStarting Hand Gesture Mode...")
        reset()
        set_mode("Hand Gesture")

        mode = create_hand_mode()

        if self.context_manager is not None:
            mode.context_manager = self.context_manager

        try:
            mode.start()
        finally:
            set_mode("Idle")

    # ========================================================
    # EYE / WINK MODE
    # ========================================================

    def run_eye_mode(self):
        print("\nStarting Eye / Wink Mode...")
        reset()
        set_mode("Eye / Wink")

        mode = create_eye_mode()

        try:
            mode.start()
        finally:
            set_mode("Idle")

    # ========================================================
    # VOICE / MAX MODE
    # ========================================================

    def run_voice_mode(self):
        print("\nStarting Voice / MAX Mode...")
        reset()
        set_mode("Voice / MAX")

        mode = create_voice_mode()

        try:
            mode.start()
        finally:
            set_mode("Idle")

    # ========================================================
    # COMMON SCREEN INTERACTION
    # ========================================================

    def screen_menu(self) -> None:
        """
        Common OCR + AI screen interaction.

        1. Read full screen
        2. Read selected area
        3. Translate selected area
        4. Summarise selected part
        5. Exit
        """

        if self.screen_service is None:

            print(
                "[SCREEN] Screen Service is unavailable."
            )

            input(
                "\nPress Enter to continue..."
            )

            return

        while True:

            print()
            print("=" * 60)
            print(" COMMON SCREEN INTERACTION")
            print("=" * 60)

            print()
            print("1. Read full screen")
            print("2. Read selected area")
            print("3. Translate selected area")
            print("4. Summarise selected part")
            print("5. Exit")
            print()

            choice = input(
                "Enter choice: "
            ).strip()

            try:

                # ------------------------------------------------
                # 1. READ FULL SCREEN
                # ------------------------------------------------

                if choice == "1":

                    print()
                    print(
                        "[SCREEN] Reading full screen..."
                    )

                    result = (
                        self.screen_service
                        .read_screen()
                    )

                    print()
                    print(
                        "[SCREEN] Result:"
                    )

                    print(
                        result
                    )

                    input(
                        "\nPress Enter to continue..."
                    )

                # ------------------------------------------------
                # 2. READ SELECTED AREA
                # ------------------------------------------------

                elif choice == "2":

                    print()
                    print(
                        "[SCREEN] Select the area to read..."
                    )

                    selected = (
                        self.screen_service
                        .select_text()
                    )

                    if not selected:

                        print(
                            "[SCREEN] No text was selected."
                        )

                        input(
                            "\nPress Enter to continue..."
                        )

                        continue

                    print()
                    print(
                        "[SCREEN] OCR completed."
                    )

                    # Use the already selected OCR text.
                    processor = (
                        self.screen_service.processor
                    )

                    if isinstance(
                        selected,
                        dict,
                    ):

                        text = selected.get(
                            "text",
                            "",
                        )

                    else:

                        text = str(selected)

                    result = (
                        processor.process_text(
                            text=text,
                            operation="read",
                            speak=True,
                        )
                    )

                    print()
                    print(
                        "[SCREEN] Result:"
                    )

                    print(
                        result
                    )

                    input(
                        "\nPress Enter to continue..."
                    )

                # ------------------------------------------------
                # 3. TRANSLATE SELECTED AREA
                # ------------------------------------------------

                elif choice == "3":

                    print()
                    print(
                        "[SCREEN] Select the area "
                        "to translate..."
                    )

                    selected = (
                        self.screen_service
                        .select_text()
                    )

                    if not selected:

                        print(
                            "[SCREEN] No text was selected."
                        )

                        input(
                            "\nPress Enter to continue..."
                        )

                        continue

                    language = input(
                        "Enter target language: "
                    ).strip()

                    if not language:

                        print(
                            "[SCREEN] Target language "
                            "is required."
                        )

                        input(
                            "\nPress Enter to continue..."
                        )

                        continue

                    if isinstance(
                        selected,
                        dict,
                    ):

                        text = selected.get(
                            "text",
                            "",
                        )

                    else:

                        text = str(selected)

                    if not text.strip():

                        print(
                            "[SCREEN] No OCR text found."
                        )

                        input(
                            "\nPress Enter to continue..."
                        )

                        continue

                    print()
                    print(
                        "[SCREEN] Translating selected text "
                        f"to {language}..."
                    )

                    processor = (
                        self.screen_service.processor
                    )

                    result = (
                        processor.process_text(
                            text=text,
                            operation="translate",
                            target_language=language,
                            speak=True,
                        )
                    )

                    print()
                    print(
                        "[SCREEN] Result:"
                    )

                    print(
                        result
                    )

                    input(
                        "\nPress Enter to continue..."
                    )

                # ------------------------------------------------
                # 4. SUMMARISE SELECTED PART
                # ------------------------------------------------

                elif choice == "4":

                    print()
                    print(
                        "[SCREEN] Select the part "
                        "to summarise..."
                    )

                    selected = (
                        self.screen_service
                        .select_text()
                    )

                    if not selected:

                        print(
                            "[SCREEN] No text was selected."
                        )

                        input(
                            "\nPress Enter to continue..."
                        )

                        continue

                    if isinstance(
                        selected,
                        dict,
                    ):

                        text = selected.get(
                            "text",
                            "",
                        )

                    else:

                        text = str(selected)

                    if not text.strip():

                        print(
                            "[SCREEN] No OCR text found."
                        )

                        input(
                            "\nPress Enter to continue..."
                        )

                        continue

                    print()
                    print(
                        "[SCREEN] Generating summary..."
                    )

                    processor = (
                        self.screen_service.processor
                    )

                    result = (
                        processor.process_text(
                            text=text,
                            operation="summarize",
                            speak=True,
                        )
                    )

                    print()
                    print(
                        "[SCREEN] Result:"
                    )

                    print(
                        result
                    )

                    input(
                        "\nPress Enter to continue..."
                    )

                # ------------------------------------------------
                # 5. EXIT SCREEN MENU
                # ------------------------------------------------

                elif choice == "5":

                    print()
                    print(
                        "[SCREEN] Returning "
                        "to main menu."
                    )

                    return

                # ------------------------------------------------
                # INVALID
                # ------------------------------------------------

                else:

                    print()
                    print(
                        "[SCREEN] Invalid choice."
                    )

                    print(
                        "Please select a number "
                        "from 1 to 5."
                    )

            except Exception as exc:

                print()
                print(
                    f"[SCREEN] Error: {exc}"
                )

                traceback.print_exc()

                input(
                    "\nPress Enter to continue..."
                )

    # ========================================================
    # CURRENT APPLICATION CONTEXT
    # ========================================================

    def show_context_status(self) -> None:
        """Display only the current application context."""

        if self.context_manager is None:

            print(
                "[CONTEXT] Context Manager unavailable."
            )

            return

        context = (
            self.context_manager
            .get_context()
        )

        print()
        print("=" * 60)
        print(" CURRENT APPLICATION CONTEXT")
        print("=" * 60)

        print()

        print(
            "Application :",
            context.get(
                "application",
                "Unknown",
            ),
        )

        print(
            "Profile     :",
            context.get(
                "profile_name",
                "default",
            ),
        )

        print(
            "Description :",
            context.get(
                "description",
                "",
            ),
        )

    # ========================================================
    # SYSTEM STATUS
    # ========================================================

    def show_system_status(self) -> None:
        """Display current system status."""

        print()
        print("=" * 60)
        print(" SYSTEM STATUS")
        print("=" * 60)

        print()

        # Context manager
        if (
            self.context_manager is not None
            and self.context_manager.is_running()
        ):

            context_status = "ACTIVE"

        else:

            context_status = "INACTIVE"

        print(
            "Context Manager :",
            context_status,
        )

        # Screen service
        if self.screen_service is not None:

            screen_status = "AVAILABLE"

        else:

            screen_status = "UNAVAILABLE"

        print(
            "Screen Service  :",
            screen_status,
        )

        # Active mode
        print(
            "Active Mode     :",
            self.active_mode_name
            or "None",
        )

    # ========================================================
    # MAIN MENU
    # ========================================================

    def show_menu(self) -> None:
        """Display the main application menu."""

        print()
        print("=" * 60)
        print(
            " MULTIMODAL TOUCHLESS HCI ENGINE"
        )
        print("=" * 60)

        # Current context
        context_name = "default"

        if self.context_manager is not None:

            context = (
                self.context_manager
                .get_context()
            )

            context_name = context.get(
                "profile_name",
                "default",
            )

        print()
        print(
            f" Current context: "
            f"{context_name.upper()}"
        )

        print()
        print("PRIMARY INTERACTION MODES")
        print("-------------------------")
        print("1. Hand Gesture Mode")
        print("2. Eye / Wink Mode")
        print("3. Voice / MAX Mode")

        print()
        print("COMMON SERVICES")
        print("---------------")
        print("4. OCR + AI Screen Service")
        print("5. Show Current Context")
        print("6. Show System Status")

        print()
        print("0. Exit")
        print()

    # ========================================================
    # MAIN LOOP
    # ========================================================

    def run(self) -> None:
        """Run the complete application."""

        self.running = True

        # Start background services
        self.start_services()

        print()
        print("=" * 60)
        print(
            " MULTIMODAL TOUCHLESS HCI ENGINE STARTED"
        )
        print("=" * 60)

        print()
        print(
            "Automatic Context Switching: ACTIVE"
        )

        while self.running:

            try:

                self.show_menu()

                choice = input(
                    "Enter choice: "
                ).strip()

                # ------------------------------------------------
                # 1. HAND
                # ------------------------------------------------

                if choice == "1":

                    self.run_hand_mode()

                # ------------------------------------------------
                # 2. EYE
                # ------------------------------------------------

                elif choice == "2":

                    self.run_eye_mode()

                # ------------------------------------------------
                # 3. VOICE
                # ------------------------------------------------

                elif choice == "3":

                    self.run_voice_mode()

                # ------------------------------------------------
                # 4. SCREEN SERVICE
                # ------------------------------------------------

                elif choice == "4":

                    self.screen_menu()

                # ------------------------------------------------
                # 5. CONTEXT
                # ------------------------------------------------

                elif choice == "5":

                    self.show_context_status()

                    input(
                        "\nPress Enter to continue..."
                    )

                # ------------------------------------------------
                # 6. SYSTEM STATUS
                # ------------------------------------------------

                elif choice == "6":

                    self.show_system_status()

                    input(
                        "\nPress Enter to continue..."
                    )

                # ------------------------------------------------
                # 0. EXIT
                # ------------------------------------------------

                elif choice == "0":

                    print()
                    print(
                        "[SYSTEM] Exit requested."
                    )

                    self.running = False

                # ------------------------------------------------
                # INVALID
                # ------------------------------------------------

                else:

                    print()
                    print(
                        "[SYSTEM] Invalid choice."
                    )

                    print(
                        "Please select a valid option."
                    )

            except KeyboardInterrupt:

                print()
                print(
                    "[SYSTEM] Keyboard interrupt received."
                )

                self.running = False

            except Exception as exc:

                print()
                print(
                    f"[SYSTEM] Main loop error: {exc}"
                )

                traceback.print_exc()

    # ========================================================
    # CLEAN SHUTDOWN
    # ========================================================

    def shutdown(self) -> None:
        """Cleanly shut down all services."""

        print()
        print("=" * 60)
        print(
            " SHUTTING DOWN TOUCHLESS HCI"
        )
        print("=" * 60)

        # ----------------------------------------------------
        # Stop active mode
        # ----------------------------------------------------

        self.stop_active_mode()

        # ----------------------------------------------------
        # Stop context manager
        # ----------------------------------------------------

        if self.context_manager is not None:

            try:

                self.context_manager.stop()

            except Exception as exc:

                print(
                    "[SYSTEM] Context shutdown error: "
                    f"{exc}"
                )

        # ----------------------------------------------------
        # Close screen service
        # ----------------------------------------------------

        if self.screen_service is not None:

            try:

                self.screen_service.close()

            except Exception as exc:

                print(
                    "[SYSTEM] Screen Service shutdown error: "
                    f"{exc}"
                )

        print()
        print(
            "[SYSTEM] All services stopped."
        )

        print(
            "[SYSTEM] Touchless HCI Engine closed."
        )


# ============================================================
# ENTRY POINT
# ============================================================

def main() -> None:
    """Application entry point."""

    application = TouchlessHCI()

    try:

        application.run()

    except Exception as exc:

        print()
        print(
            "[SYSTEM] Fatal error:"
        )

        print(
            exc
        )

        traceback.print_exc()

    finally:

        application.shutdown()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()

