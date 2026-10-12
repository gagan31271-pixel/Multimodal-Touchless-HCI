# utils/telemetry.py

from pathlib import Path
from collections import deque
import json
import os
import tempfile
import threading
import time


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TELEMETRY_FILE = PROJECT_ROOT / "runtime_metrics.json"

_lock = threading.Lock()

_frame_times = deque(maxlen=120)

_last_gesture = None
_last_disk_write = 0.0

WRITE_INTERVAL = 0.5


_data = {
    "mode": "Idle",
    "context": "DEFAULT",
    "fps": None,
    "latency_ms": None,
    "inference_ms": None,
    "gesture": "None",
    "gesture_counts": {},
    "gesture_accuracy": {},
    "updated_at": 0,
}


# ============================================================
# LOAD EXISTING DATA ONCE
# ============================================================

def _load_initial_data():

    global _data

    try:

        if TELEMETRY_FILE.exists():

            with open(
                TELEMETRY_FILE,
                "r",
                encoding="utf-8",
            ) as file:

                loaded = json.load(file)

            if isinstance(loaded, dict):

                _data.update(loaded)

    except Exception:
        pass


# ============================================================
# WRITE TO DISK
# ============================================================

def _write_file():

    TELEMETRY_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fd, temp_path = tempfile.mkstemp(
        prefix="runtime_metrics_",
        suffix=".json",
        dir=str(TELEMETRY_FILE.parent),
    )

    try:

        with os.fdopen(
            fd,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                _data,
                file,
                indent=2,
            )

        os.replace(
            temp_path,
            TELEMETRY_FILE,
        )

    except Exception:

        try:
            os.remove(temp_path)
        except OSError:
            pass


# ============================================================
# PERIODIC DISK WRITE
# ============================================================

def _flush_if_needed(force=False):

    global _last_disk_write

    now = time.monotonic()

    if (
        force
        or now - _last_disk_write
        >= WRITE_INTERVAL
    ):

        _data["updated_at"] = time.time()

        _write_file()

        _last_disk_write = now


# ============================================================
# UPDATE TELEMETRY
# ============================================================

def update(
    force=False,
    **kwargs,
):

    with _lock:

        _data.update(kwargs)

        _flush_if_needed(
            force=force
        )


# ============================================================
# MODE
# ============================================================

def set_mode(mode):

    update(
        force=True,
        mode=str(mode),
    )


# ============================================================
# CONTEXT
# ============================================================

def set_context(context):

    update(
        force=True,
        context=str(context),
    )


# ============================================================
# GESTURE
# ============================================================

def set_gesture(gesture):

    update(
        gesture=str(gesture),
    )


# ============================================================
# RECORD GESTURE
# ============================================================

def record_gesture(gesture):

    global _last_gesture

    if gesture is None:

        gesture = "None"

    gesture = str(gesture)

    with _lock:

        _data["gesture"] = gesture

        # Count only when gesture changes.
        if gesture != _last_gesture:

            if gesture.lower() not in {
                "none",
                "neutral",
                "fist",
            }:

                counts = _data.setdefault(
                    "gesture_counts",
                    {},
                )

                counts[gesture] = (
                    counts.get(
                        gesture,
                        0,
                    )
                    + 1
                )

            _last_gesture = gesture

        _flush_if_needed()


# ============================================================
# RECORD FRAME
# ============================================================

def record_frame(
    mode=None,
    gesture=None,
    processing_ms=None,
    inference_ms=None,
):

    now = time.perf_counter()

    _frame_times.append(now)

    fps = None

    if len(_frame_times) >= 2:

        elapsed = (
            _frame_times[-1]
            - _frame_times[0]
        )

        if elapsed > 0:

            fps = (
                len(_frame_times) - 1
            ) / elapsed

    with _lock:

        if mode is not None:

            _data["mode"] = str(
                mode
            )

        if processing_ms is not None:

            _data["latency_ms"] = round(
                processing_ms,
                2,
            )

        if inference_ms is not None:

            _data["inference_ms"] = round(
                inference_ms,
                2,
            )

        if fps is not None:

            _data["fps"] = round(
                fps,
                2,
            )

        if gesture is not None:

            gesture = str(
                gesture
            )

            _data["gesture"] = gesture

            if gesture != _last_gesture:

                if gesture.lower() not in {
                    "none",
                    "neutral",
                    "fist",
                }:

                    counts = _data.setdefault(
                        "gesture_counts",
                        {},
                    )

                    counts[gesture] = (
                        counts.get(
                            gesture,
                            0,
                        )
                        + 1
                    )

                globals()["_last_gesture"] = (
                    gesture
                )

        _flush_if_needed()


# ============================================================
# RESET
# ============================================================

def reset():

    global _last_gesture
    global _last_disk_write

    with _lock:

        _frame_times.clear()

        _last_gesture = None

        _last_disk_write = 0.0

        _data.clear()

        _data.update(
            {
                "mode": "Idle",
                "context": "DEFAULT",
                "fps": None,
                "latency_ms": None,
                "inference_ms": None,
                "gesture": "None",
                "gesture_counts": {},
                "gesture_accuracy": {},
                "updated_at": 0,
            }
        )

        _flush_if_needed(
            force=True
        )


# ============================================================
# INITIALIZE
# ============================================================

_load_initial_data()

try:

    with _lock:

        _flush_if_needed(
            force=True
        )

except Exception:
    pass