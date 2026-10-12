# ============================================================
# AVAILABLE TTS VOICES TEST
# ============================================================

import os
import sys

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

sys.path.insert(
    0,
    PROJECT_ROOT
)

from modules.speech_engine import (
    SpeechEngine
)


def main():

    speech = SpeechEngine()

    print()
    print("=" * 75)
    print("                  AVAILABLE TTS VOICES")
    print("=" * 75)
    print()

    voices = speech.get_voice_info()

    if not voices:

        print(
            "No Windows SAPI voices found."
        )

        speech.close()

        return

    for number, voice in enumerate(
        voices,
        start=1
    ):

        print(
            f"{number}. Name: "
            f"{voice['name']}"
        )

        print(
            f"   ID: "
            f"{voice['id']}"
        )

        print()

    print("=" * 75)

    print(
        f"Total voices available: "
        f"{len(voices)}"
    )

    print("=" * 75)

    print()

    print(
        f"Active voice: "
        f"{speech.get_active_voice_name()}"
    )

    speech.close()


if __name__ == "__main__":

    main()