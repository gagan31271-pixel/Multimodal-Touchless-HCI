# ============================================================
# CONTEXT-AWARE OCR + AI TEST
#
# Select text -> choose Read / Translate / Summarize
# ============================================================

import os
import sys
import time

# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

sys.path.insert(
    0,
    PROJECT_ROOT
)

# ============================================================
# IMPORTS
# ============================================================

from modules.ai_screen_processor import (
    AIScreenProcessor
)

from config import (
    AI_SCREEN_TARGET_LANGUAGE,
)


# ============================================================
# PRINT RESULT
# ============================================================

def print_result(result):

    print()
    print("=" * 75)
    print("CONTEXT ACTION RESULT")
    print("=" * 75)
    print()

    if result.get(
        "cancelled",
        False
    ):

        print(
            "Selection cancelled."
        )

        return

    if not result.get(
        "success",
        False
    ):

        print(
            f"Error: "
            f"{result.get('error', 'Unknown error')}"
        )

        return

    print(
        f"Operation: "
        f"{result.get('operation', '')}"
    )

    print()

    print("SELECTED OCR TEXT")

    print("-" * 75)

    print(
        result.get(
            "input_text",
            ""
        )
    )

    print()

    print("RESULT")

    print("-" * 75)

    print(
        result.get(
            "result",
            ""
        )
    )

    print()

    if result.get(
        "translation"
    ):

        print("TRANSLATION")

        print("-" * 75)

        print(
            result["translation"]
        )

        print()

    if result.get(
        "summary"
    ):

        print("SUMMARY")

        print("-" * 75)

        print(
            result["summary"]
        )

        print()

    print(
        f"OCR confidence: "
        f"{result.get('ocr_confidence', 0.0):.2f}%"
    )

    print(
        f"Words detected: "
        f"{result.get('word_count', 0)}"
    )

    print("=" * 75)


# ============================================================
# MAIN
# ============================================================

def main():

    print()

    print("=" * 75)

    print(
        "       CONTEXT-AWARE OCR + AI ACTION TEST"
    )

    print("=" * 75)

    print()

    print(
        "Workflow:"
    )

    print(
        "Screen -> Select Region -> OCR -> Action"
    )

    print()

    print(
        "Target translation language: "
        f"{AI_SCREEN_TARGET_LANGUAGE}"
    )

    print()

    print(
        "Actions:"
    )

    print(
        "1. Read selected text"
    )

    print(
        "2. Translate selected text"
    )

    print(
        "3. Summarize selected text"
    )

    print()

    processor = (
        AIScreenProcessor()
    )

    try:

        # ----------------------------------------------------
        # Select text FIRST
        # ----------------------------------------------------

        print(
            "Open the webpage/document now."
        )

        print()

        print(
            "A selection window will appear."
        )

        print(
            "Drag around the text you want."
        )

        print(
            "Press ENTER."
        )

        print()

        time.sleep(2)

        selection = (
            processor.select_text()
        )

        # ----------------------------------------------------
        # Selection cancelled
        # ----------------------------------------------------

        if selection.get(
            "cancelled",
            False
        ):

            print()

            print(
                "Selection cancelled."
            )

            return

        # ----------------------------------------------------
        # Selection failed
        # ----------------------------------------------------

        if not selection.get(
            "success",
            False
        ):

            print()

            print(
                f"OCR error: "
                f"{selection.get('error', 'Unknown error')}"
            )

            return

        # ----------------------------------------------------
        # Show OCR result
        # ----------------------------------------------------

        print()

        print("=" * 75)

        print(
            "OCR SELECTION SUCCESSFUL"
        )

        print("=" * 75)

        print()

        print(
            "Selected text:"
        )

        print(
            selection["text"]
        )

        print()

        print(
            f"Words detected: "
            f"{selection['word_count']}"
        )

        print(
            f"OCR confidence: "
            f"{selection['ocr_confidence']:.2f}%"
        )

        print()

        # ----------------------------------------------------
        # Action menu
        # ----------------------------------------------------

        print(
            "Choose an action:"
        )

        print()

        print(
            "1. Read"
        )

        print(
            "2. Translate"
        )

        print(
            "3. Summarize"
        )

        print()

        choice = input(
            "Enter choice (1-3): "
        ).strip()

        print()

        # ----------------------------------------------------
        # READ
        # ----------------------------------------------------

        if choice == "1":

            result = (
                processor.process_text(
                    text=selection["text"],
                    operation="read",
                    speak=True,
                )
            )

        # ----------------------------------------------------
        # TRANSLATE
        # ----------------------------------------------------

        elif choice == "2":

            result = (
                processor.process_text(
                    text=selection["text"],
                    operation="translate",
                    target_language=(
                        AI_SCREEN_TARGET_LANGUAGE
                    ),
                    speak=True,
                )
            )

        # ----------------------------------------------------
        # SUMMARIZE
        # ----------------------------------------------------

        elif choice == "3":

            result = (
                processor.process_text(
                    text=selection["text"],
                    operation="summarize",
                    speak=True,
                )
            )

        else:

            print(
                "Invalid choice."
            )

            return

        # ----------------------------------------------------
        # Add OCR information
        # ----------------------------------------------------

        result["ocr_confidence"] = (
            selection["ocr_confidence"]
        )

        result["word_count"] = (
            selection["word_count"]
        )

        # ----------------------------------------------------
        # Display
        # ----------------------------------------------------

        print_result(
            result
        )

    except KeyboardInterrupt:

        print()

        print(
            "Context-aware AI test interrupted."
        )

    except Exception as error:

        print()

        print(
            f"Context-aware AI error: "
            f"{error}"
        )

    finally:

        processor.close()

        print()

        print(
            "AI screen processor stopped."
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()