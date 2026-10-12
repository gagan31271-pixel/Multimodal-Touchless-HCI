# ============================================================
# AI ENGINE TEST
# ============================================================

import os
import sys

# ------------------------------------------------------------
# Project root
# ------------------------------------------------------------

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

sys.path.insert(
    0,
    PROJECT_ROOT
)

from modules.ai_engine import AIEngine


SAMPLE_TEXT = """
Multimodal Touchless Human Computer Interaction Engine.

The system uses hand gestures, eye blink detection,
facial expressions and voice commands to control a computer.

The system also provides OCR based screen reading,
text summarization, translation and auditory feedback.

Automatic context switching detects the active application
and changes gesture mappings according to the application.
"""


def main():

    print()

    print("=" * 70)

    print(
        "                 AI ENGINE TEST"
    )

    print("=" * 70)

    print()

    ai = AIEngine()

    print(
        f"Provider: {ai.get_provider()}"
    )

    print()

    # ========================================================
    # SUMMARY
    # ========================================================

    print(
        "Generating summary..."
    )

    try:

        summary = ai.summarize(
            SAMPLE_TEXT
        )

        print()

        print(
            "SUMMARY"
        )

        print("-" * 70)

        print(summary)

        print("-" * 70)

    except Exception as error:

        print()

        print(
            f"Summary error: {error}"
        )

        print()

        print(
            "Check that the selected AI provider "
            "is installed and running."
        )

        return

    # ========================================================
    # TRANSLATION
    # ========================================================

    print()

    print(
        "Generating translation..."
    )

    try:

        translation = ai.translate(
            SAMPLE_TEXT,
            target_language="Kannada"
        )

        print()

        print(
            "TRANSLATION"
        )

        print("-" * 70)

        print(translation)

        print("-" * 70)

    except Exception as error:

        print()

        print(
            f"Translation error: {error}"
        )

        return

    print()

    print(
        "AI test completed successfully."
    )

    print()


if __name__ == "__main__":

    main()