# ============================================================
# CONTEXT ACTION UI TEST
#
# Select OCR text once -> Read / Translate / Summarize
# ============================================================

import os
import sys
import time


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

sys.path.insert(
    0,
    PROJECT_ROOT,
)


# ============================================================
# IMPORTS
# ============================================================

from modules.ai_screen_processor import (
    AIScreenProcessor
)

from modules.ocr_screen.context_action_menu import (
    ContextActionMenu
)

from config import (
    AI_SCREEN_TARGET_LANGUAGE,
)


# ============================================================
# MAIN
# ============================================================

def main():

    print()

    print("=" * 75)

    print(
        "       CONTEXT-AWARE OCR ACTION UI TEST"
    )

    print("=" * 75)

    print()

    print(
        "Workflow:"
    )

    print(
        "Select Region -> OCR -> Context Action Menu"
    )

    print()

    print(
        "Actions:"
    )

    print(
        "Read / Translate / Summarize"
    )

    print()

    processor = (
        AIScreenProcessor()
    )

    try:

        print(
            "Open the webpage or document."
        )

        print()

        print(
            "Select the text region."
        )

        print(
            "Press ENTER after selecting."
        )

        print()

        time.sleep(2)

        # ----------------------------------------------------
        # OCR ONLY
        # ----------------------------------------------------

        selection = (
            processor.select_text()
        )

        if selection.get(
            "cancelled",
            False,
        ):

            print(
                "Selection cancelled."
            )

            return

        if not selection.get(
            "success",
            False,
        ):

            print(
                "OCR failed:"
            )

            print(
                selection.get(
                    "error",
                    "Unknown error.",
                )
            )

            return

        # ----------------------------------------------------
        # SHOW CONTEXT MENU
        # ----------------------------------------------------

        menu = ContextActionMenu(
            processor=processor,
            target_language=(
                AI_SCREEN_TARGET_LANGUAGE
            ),
        )

        menu.show(
            selected_text=selection["text"],
            ocr_confidence=(
                selection[
                    "ocr_confidence"
                ]
            ),
            word_count=(
                selection[
                    "word_count"
                ]
            ),
        )

    except KeyboardInterrupt:

        print()

        print(
            "Context action test interrupted."
        )

    except Exception as error:

        print()

        print(
            f"Context action error: {error}"
        )

    finally:

        processor.close()

        print()

        print(
            "Context action test stopped."
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()