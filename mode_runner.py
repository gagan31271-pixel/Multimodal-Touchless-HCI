"""
Multimodal Touchless HCI
Mode Runner

Runs exactly ONE interaction mode at a time.
"""

from __future__ import annotations

import sys
import traceback


# ============================================================
# HAND GESTURE MODE
# ============================================================

def run_hand():

    from modules.hand_gesture.hand_mouse import HandGestureMouse

    print("\n[MODE RUNNER] Starting Hand Gesture Mode...")

    controller = HandGestureMouse()

    try:
        controller.start()

    except KeyboardInterrupt:
        print("\n[MODE RUNNER] Hand mode interrupted.")

    finally:
        try:
            controller.stop()
        except Exception:
            pass


# ============================================================
# EYE / WINK MODE
# ============================================================

def run_eye():

    from modules.multimodal.eye_mode import EyeMode

    print("\n[MODE RUNNER] Starting Eye / Wink Mode...")

    controller = EyeMode()

    try:
        controller.start()

    except KeyboardInterrupt:
        print("\n[MODE RUNNER] Eye mode interrupted.")

    finally:
        try:
            controller.stop()
        except Exception:
            pass


# ============================================================
# MAX / VOICE MODE
# ============================================================

def run_max():

    from modules.voice_command.max import MAX

    print("\n[MODE RUNNER] Starting MAX / Voice Mode...")

    assistant = MAX()

    try:
        assistant.run()

    except KeyboardInterrupt:
        print("\n[MODE RUNNER] MAX interrupted.")

    finally:
        try:
            assistant.shutdown()
        except Exception:
            pass


# ============================================================
# MAIN
# ============================================================

def main():

    if len(sys.argv) < 2:

        print()
        print("Usage:")
        print("  python mode_runner.py hand")
        print("  python mode_runner.py eye")
        print("  python mode_runner.py max")
        print()

        return

    mode = sys.argv[1].lower().strip()

    try:

        if mode == "hand":
            run_hand()

        elif mode == "eye":
            run_eye()

        elif mode == "max":
            run_max()

        else:

            print(
                f"[MODE RUNNER] Unknown mode: {mode}"
            )

    except Exception as exc:

        print()
        print(
            f"[MODE RUNNER] Error in {mode} mode:"
        )
        print(exc)
        print()

        traceback.print_exc()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()