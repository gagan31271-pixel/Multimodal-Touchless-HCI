# ============================================================
# AI SCREEN PROCESSOR
#
# OCR -> Context Action -> Read / Translate / Summarize
# ============================================================

from modules.ocr_screen.screen_reader import ScreenReader
from modules.ai_engine import AIEngine

from config import (
    AI_SCREEN_TARGET_LANGUAGE,
    AI_SCREEN_TTS,
)


class AIScreenProcessor:

    def __init__(self):

        self.screen_reader = ScreenReader()

        self.ai = AIEngine()

        self.last_ocr_text = ""

        self.last_translation = ""

        self.last_summary = ""

        self.last_ai_result = ""

        self.last_operation = "None"

        self.last_error = ""

    # ========================================================
    # PROCESS TEXT
    # ========================================================

    def process_text(
        self,
        text,
        operation="summarize",
        target_language=None,
        speak=None,
    ):

        self.last_error = ""

        if not text or not str(text).strip():

            self.last_error = (
                "No text available for processing."
            )

            return {
                "success": False,
                "operation": operation,
                "input_text": "",
                "translation": "",
                "summary": "",
                "result": "",
                "error": self.last_error,
            }

        text = str(text).strip()

        self.last_ocr_text = text

        operation = (
            str(operation)
            .strip()
            .lower()
        )

        if target_language is None:

            target_language = (
                AI_SCREEN_TARGET_LANGUAGE
            )

        if speak is None:

            speak = AI_SCREEN_TTS

        self.last_translation = ""
        self.last_summary = ""
        self.last_ai_result = ""

        # ====================================================
        # READ
        # ====================================================

        if operation in (
            "read",
            "speak",
            "tts",
        ):

            try:

                self.last_ai_result = text

                self.last_operation = "Read"

                if speak:

                    self.screen_reader.speak_text(
                        text
                    )

                return {
                    "success": True,
                    "operation": "Read",
                    "input_text": text,
                    "translation": "",
                    "summary": "",
                    "result": text,
                    "error": "",
                }

            except Exception as error:

                self.last_error = str(
                    error
                )

                return {
                    "success": False,
                    "operation": "Read",
                    "input_text": text,
                    "translation": "",
                    "summary": "",
                    "result": "",
                    "error": self.last_error,
                }

        # ====================================================
        # SUMMARIZE
        # ====================================================

        if operation in (
            "summarize",
            "summary",
        ):

            try:

                summary = (
                    self.ai.summarize(
                        text,
                        output_language="English",
                    )
                )

                self.last_summary = summary

                self.last_ai_result = summary

                self.last_operation = (
                    "Summarization"
                )

                if (
                    speak
                    and
                    summary
                ):

                    self.screen_reader.speak_text(
                        summary
                    )

                return {
                    "success": True,
                    "operation": "Summarization",
                    "input_text": text,
                    "translation": "",
                    "summary": summary,
                    "result": summary,
                    "error": "",
                }

            except Exception as error:

                self.last_error = str(
                    error
                )

                return {
                    "success": False,
                    "operation": "Summarization",
                    "input_text": text,
                    "translation": "",
                    "summary": "",
                    "result": "",
                    "error": self.last_error,
                }

        # ====================================================
        # TRANSLATE
        # ====================================================

        if operation in (
            "translate",
            "translation",
        ):

            try:

                translation = (
                    self.ai.translate(
                        text,
                        target_language=(
                            target_language
                        ),
                    )
                )

                self.last_translation = (
                    translation
                )

                self.last_ai_result = (
                    translation
                )

                self.last_operation = (
                    "Translation"
                )

                if (
                    speak
                    and
                    translation
                ):

                    self.screen_reader.speak_text(
                        translation
                    )

                return {
                    "success": True,
                    "operation": "Translation",
                    "input_text": text,
                    "translation": translation,
                    "summary": "",
                    "result": translation,
                    "error": "",
                }

            except Exception as error:

                self.last_error = str(
                    error
                )

                return {
                    "success": False,
                    "operation": "Translation",
                    "input_text": text,
                    "translation": "",
                    "summary": "",
                    "result": "",
                    "error": self.last_error,
                }

        # ====================================================
        # UNSUPPORTED OPERATION
        # ====================================================

        self.last_error = (
            f"Unsupported AI operation: "
            f"{operation}"
        )

        return {
            "success": False,
            "operation": operation,
            "input_text": text,
            "translation": "",
            "summary": "",
            "result": "",
            "error": self.last_error,
        }

    # ========================================================
    # SELECT TEXT ONLY
    #
    # This is the important method for the future
    # contextual action menu.
    #
    # It selects a region and performs OCR only.
    # Nothing is spoken or sent to AI here.
    # ========================================================

    def select_text(self):

        ocr_result = (
            self.screen_reader
            .select_and_extract_text()
        )

        if ocr_result.get(
            "cancelled",
            False
        ):

            return {
                "success": False,
                "cancelled": True,
                "text": "",
                "word_count": 0,
                "ocr_confidence": 0.0,
                "error": "Selection cancelled.",
            }

        text = (
            ocr_result
            .get("text", "")
            .strip()
        )

        if not text:

            return {
                "success": False,
                "cancelled": False,
                "text": "",
                "word_count": (
                    ocr_result.get(
                        "word_count",
                        0,
                    )
                ),
                "ocr_confidence": (
                    ocr_result.get(
                        "average_confidence",
                        0.0,
                    )
                ),
                "error": (
                    "No readable text detected "
                    "in selected region."
                ),
            }

        self.last_ocr_text = text

        return {
            "success": True,
            "cancelled": False,
            "text": text,
            "word_count": (
                ocr_result.get(
                    "word_count",
                    0,
                )
            ),
            "ocr_confidence": (
                ocr_result.get(
                    "average_confidence",
                    0.0,
                )
            ),
            "error": "",
        }

    # ========================================================
    # PROCESS FULL SCREEN
    # ========================================================

    def process_full_screen(
        self,
        operation="summarize",
        target_language=None,
        speak=None,
    ):

        ocr_result = (
            self.screen_reader.read_screen(
                speak=False
            )
        )

        text = (
            ocr_result.get(
                "text",
                ""
            )
            .strip()
        )

        if not text:

            return {
                "success": False,
                "operation": operation,
                "input_text": "",
                "translation": "",
                "summary": "",
                "result": "",
                "ocr_confidence": (
                    ocr_result.get(
                        "average_confidence",
                        0.0,
                    )
                ),
                "word_count": (
                    ocr_result.get(
                        "word_count",
                        0,
                    )
                ),
                "error": (
                    "No readable text detected."
                ),
            }

        result = self.process_text(
            text=text,
            operation=operation,
            target_language=target_language,
            speak=speak,
        )

        result["ocr_confidence"] = (
            ocr_result.get(
                "average_confidence",
                0.0,
            )
        )

        result["word_count"] = (
            ocr_result.get(
                "word_count",
                0,
            )
        )

        return result

    # ========================================================
    # PROCESS SELECTED REGION
    #
    # Compatibility wrapper.
    #
    # Selects a region, performs OCR, then performs
    # the requested action.
    # ========================================================

    def process_selected_region(
        self,
        operation="summarize",
        target_language=None,
        speak=None,
    ):

        selection = self.select_text()

        if not selection["success"]:

            return {
                "success": False,
                "cancelled": (
                    selection["cancelled"]
                ),
                "operation": operation,
                "input_text": "",
                "translation": "",
                "summary": "",
                "result": "",
                "ocr_confidence": (
                    selection[
                        "ocr_confidence"
                    ]
                ),
                "word_count": (
                    selection[
                        "word_count"
                    ]
                ),
                "error": (
                    selection["error"]
                ),
            }

        result = self.process_text(
            text=selection["text"],
            operation=operation,
            target_language=target_language,
            speak=speak,
        )

        result["cancelled"] = False

        result["ocr_confidence"] = (
            selection[
                "ocr_confidence"
            ]
        )

        result["word_count"] = (
            selection[
                "word_count"
            ]
        )

        return result

    # ========================================================
    # READ SELECTED
    # ========================================================

    def read_selected(self):

        return self.process_selected_region(
            operation="read",
            speak=True,
        )

    # ========================================================
    # SUMMARIZE SCREEN
    # ========================================================

    def summarize_screen(
        self,
        speak=None,
    ):

        return self.process_full_screen(
            operation="summarize",
            speak=speak,
        )

    # ========================================================
    # TRANSLATE SCREEN
    # ========================================================

    def translate_screen(
        self,
        target_language=None,
        speak=None,
    ):

        return self.process_full_screen(
            operation="translate",
            target_language=target_language,
            speak=speak,
        )

    # ========================================================
    # SUMMARIZE SELECTED
    # ========================================================

    def summarize_selected(
        self,
        speak=None,
    ):

        return self.process_selected_region(
            operation="summarize",
            speak=speak,
        )

    # ========================================================
    # TRANSLATE SELECTED
    # ========================================================

    def translate_selected(
        self,
        target_language=None,
        speak=None,
    ):

        return self.process_selected_region(
            operation="translate",
            target_language=target_language,
            speak=speak,
        )

    # ========================================================
    # PROCESS THE LAST SELECTED TEXT
    #
    # Useful for the future contextual action menu.
    # ========================================================

    def process_last_selected(
        self,
        operation,
        target_language=None,
        speak=None,
    ):

        if not self.last_ocr_text:

            return {
                "success": False,
                "operation": operation,
                "input_text": "",
                "translation": "",
                "summary": "",
                "result": "",
                "error": (
                    "No selected OCR text available."
                ),
            }

        return self.process_text(
            text=self.last_ocr_text,
            operation=operation,
            target_language=target_language,
            speak=speak,
        )

    # ========================================================
    # STATUS
    # ========================================================

    def get_status(self):

        return {
            "operation": self.last_operation,
            "ocr_text": self.last_ocr_text,
            "translation": self.last_translation,
            "summary": self.last_summary,
            "ai_result": self.last_ai_result,
            "error": self.last_error,
        }

    # ========================================================
    # CLOSE
    # ========================================================

    def close(self):

        self.screen_reader.close()