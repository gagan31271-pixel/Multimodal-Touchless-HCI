from __future__ import annotations

from modules.ai_screen_processor import AIScreenProcessor


class ScreenService:
    """
    Shared screen interaction service.

    This service is available to every interaction mode:
        - Hand Gesture
        - Eye / Wink
        - Voice / MAX

    It owns ONE AIScreenProcessor instance so OCR/AI logic
    is not duplicated across the project.
    """

    def __init__(self) -> None:

        self.processor = AIScreenProcessor()

        self.last_text = ""

    # ============================================================
    # FULL SCREEN
    # ============================================================

    def read_screen(self) -> str | None:

        result = self.processor.process_full_screen(
            operation="read",
            speak=True,
        )

        return result

    def summarize_screen(self) -> str | None:

        result = self.processor.process_full_screen(
            operation="summarize",
            speak=True,
        )

        return result

    def translate_screen(
        self,
        target_language: str = "Kannada",
    ) -> str | None:

        result = self.processor.process_full_screen(
            operation="translate",
            target_language=target_language,
            speak=True,
        )

        return result

    # ============================================================
    # SELECTED REGION
    # ============================================================

    def select_text(self) -> str | None:

        text = self.processor.select_text()

        if text:
            self.last_text = text

        return text

    def read_selected(self) -> str | None:

        return self.processor.read_selected()

    def summarize_selected(self) -> str | None:

        return self.processor.summarize_selected()

    def translate_selected(
        self,
        target_language: str = "Kannada",
    ) -> str | None:

        return self.processor.translate_selected(
            target_language=target_language
        )

    # ============================================================
    # COMMON CONTEXT MENU
    # ============================================================

    def open_context_menu(self) -> None:
       

        try:

            # ====================================================
            # ONE AND ONLY ONE SCREEN SELECTION
            # ====================================================

            selected = self.processor.select_text()

            if not selected:
                print(
                    "[SCREEN] No text was selected."
                )
                return

            # AIScreenProcessor returns OCR information
            if isinstance(selected, dict):

                text = selected.get(
                    "text",
                    ""
                )

            else:

                text = str(selected)

            if not text.strip():

                print(
                    "[SCREEN] OCR returned no text."
                )
                return

            self.last_text = text

            # ====================================================
            # DISPLAY SELECTED TEXT
            # ====================================================

            print()
            print("=" * 60)
            print("SELECTED TEXT")
            print("=" * 60)
            print(text)
            print("=" * 60)

            print("1. Read")
            print("2. Translate")
            print("3. Summarize")
            print("0. Cancel")

            choice = input(
                "Select action: "
            ).strip()

            # ====================================================
            # READ
            # ====================================================

            if choice == "1":

                result = self.processor.process_text(
                    text=text,
                    operation="read",
                    speak=True,
                )

                print()
                print("=" * 60)
                print("READ RESULT")
                print("=" * 60)
                print(result)
                print("=" * 60)

            # ====================================================
            # TRANSLATE
            # ====================================================

            elif choice == "2":

                language = input(
                    "Target language (default Kannada): "
                ).strip()

                if not language:
                    language = "Kannada"

                # IMPORTANT:
                # Use the already-selected OCR text.
                # Do NOT call translate_selected().
                result = self.processor.process_text(
                    text=text,
                    operation="translate",
                    target_language=language,
                    speak=True,
                )

                print()
                print("=" * 60)
                print("TRANSLATION RESULT")
                print("=" * 60)
                print(result)
                print("=" * 60)

            # ====================================================
            # SUMMARIZE
            # ====================================================

            elif choice == "3":

                # IMPORTANT:
                # Use the already-selected OCR text.
                result = self.processor.process_text(
                    text=text,
                    operation="summarize",
                    speak=True,
                )

                print()
                print("=" * 60)
                print("SUMMARY RESULT")
                print("=" * 60)
                print(result)
                print("=" * 60)

            # ====================================================
            # CANCEL
            # ====================================================

            elif choice == "0":

                print(
                    "[SCREEN] Operation cancelled."
                )

            else:

                print(
                    "[SCREEN] Invalid option."
                )

        except Exception as exc:

            print(
                f"[SCREEN] Context action error: {exc}"
            )  
    # ============================================================
    # STATUS
    # ============================================================

    def get_status(self):

        return self.processor.get_status()

    # ============================================================
    # CLOSE
    # ============================================================

    def close(self) -> None:

        try:

            self.processor.close()

        except Exception as exc:

            print(
                f"[SCREEN] Close error: {exc}"
            )