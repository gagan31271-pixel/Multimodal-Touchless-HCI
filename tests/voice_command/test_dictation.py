from pynput import keyboard

from modules.voice_command.dictation_engine import (
    DictationEngine,
)


def main():

    print()
    print("=" * 55)
    print(" WHISPER DICTATION TEST")
    print("=" * 55)
    print()
    print("1. Open Notepad.")
    print("2. Click inside the text area.")
    print("3. Speak normally.")
    print("4. Each completed speech segment will be typed.")
    print()
    print(">>> PRESS F8 AT ANY TIME TO STOP DICTATION <<<")
    print()

    engine = DictationEngine(
        model_name="base",
        max_segment_seconds=8.0,
        silence_seconds=0.9,
    )

    # ------------------------------------------------------
    # Global keyboard stop
    # ------------------------------------------------------

    def on_press(key):

        if key == keyboard.Key.f8:

            print()
            print("[TEST] F8 pressed.")
            print("[TEST] Stopping dictation...")

            engine.stop()

            return False

        return True

    listener = keyboard.Listener(
        on_press=on_press
    )

    listener.start()

    # ------------------------------------------------------
    # Start dictation
    # ------------------------------------------------------

    engine.start()

    try:

        # Do not block indefinitely.
        while engine.running:

            if not listener.is_alive():
                break

            listener.join(
                timeout=0.2
            )

    except KeyboardInterrupt:

        print()
        print("[TEST] Ctrl+C detected.")

        engine.stop()

    finally:

        engine.stop()

        if engine.thread is not None:

            engine.thread.join(
                timeout=2.0
            )

        if listener.is_alive():

            listener.stop()

            listener.join(
                timeout=1.0
            )

        print()
        print("[TEST] Dictation terminated safely.")
        print()


if __name__ == "__main__":
    main()