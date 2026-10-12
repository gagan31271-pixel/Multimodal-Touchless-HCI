# ============================================================
# SELECTIVE OCR TEST
# ============================================================

import os
import sys
import time

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

sys.path.insert(
    0,
    PROJECT_ROOT
)

from modules.ocr_screen.screen_reader import (
    ScreenReader
)


def main():

    print()

    print("=" * 70)
    print("                 SELECTIVE OCR TEST")
    print("=" * 70)

    print()

    print(
        "1. Open the webpage/document you want to read."
    )

    print(
        "2. A full-screen selection window will appear."
    )

    print(
        "3. Drag around ONLY the text you want."
    )

    print(
        "4. Press ENTER."
    )

    print(
        "5. The selected region will be OCR'd."
    )

    print(
        "6. The recognized text will be spoken."
    )

    print()

    print(
        "Press ESC to cancel."
    )

    print("=" * 70)

    time.sleep(2)

    reader = ScreenReader()

    try:

        result = reader.select_region()

        if result.get("cancelled", False):

            print()
            print("Selection cancelled.")
            return

        print()

        print("=" * 70)
        print("SELECTED REGION OCR RESULT")
        print("=" * 70)

        print()

        print(
            result.get(
                "text",
                ""
            )
        )

        print()

        print("-" * 70)

        print(
            f"Words detected: "
            f"{result.get('word_count', 0)}"
        )

        print(
            f"Average confidence: "
            f"{result.get('average_confidence', 0.0):.2f}%"
        )

        print("-" * 70)

        print()

        print(
            "Selective OCR completed successfully."
        )

    except KeyboardInterrupt:

        print()
        print("Test interrupted.")

    except Exception as error:

        print()
        print("=" * 70)
        print("SELECTIVE OCR TEST FAILED")
        print("=" * 70)
        print()
        print(f"Error: {error}")

    finally:

        reader.close()


if __name__ == "__main__":
    main()