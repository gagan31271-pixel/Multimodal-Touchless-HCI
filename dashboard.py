"""
Multimodal Touchless HCI
Performance Dashboard
======================

Run with:

    streamlit run dashboard.py

Dashboard displays:
    - Active application
    - Current context
    - CPU usage
    - RAM usage
    - FPS
    - Latency
    - Gesture accuracy status
    - Gesture usage
    - System information
"""

from __future__ import annotations

import json
import platform
import time
from pathlib import Path
from typing import Any, Dict

import psutil
import pygetwindow as gw
import streamlit as st


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent

TELEMETRY_FILE = (
    PROJECT_ROOT
    / "runtime_metrics.json"
)

REFRESH_SECONDS = 1.0

TARGET_FPS = 30.0
TARGET_LATENCY_MS = 30.0


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Multimodal Touchless HCI Dashboard",
    page_icon="🖐️",
    layout="wide",
)


# ============================================================
# HELPERS
# ============================================================

def safe_number(
    value: Any,
    default: float = 0.0,
) -> float:

    try:
        return float(value)

    except (
        TypeError,
        ValueError,
    ):
        return default


def get_active_window() -> str:
    """Return active Windows application title."""

    try:

        window = gw.getActiveWindow()

        if window is None:
            return "Unknown"

        title = window.title

        if not title:
            return "Unknown"

        return title.strip()

    except Exception:

        return "Unknown"


def detect_context(
    title: str,
) -> str:
    """Detect a simple application context."""

    title_lower = title.lower()

    if any(
        x in title_lower
        for x in [
            "visual studio code",
            "vs code",
            "pycharm",
            "intellij",
            "android studio",
            "eclipse",
            "cursor",
        ]
    ):
        return "coding"

    if any(
        x in title_lower
        for x in [
            "microsoft edge",
            "google chrome",
            "chrome",
            "firefox",
            "brave",
            "opera",
        ]
    ):
        return "browser"

    if any(
        x in title_lower
        for x in [
            "powerpoint",
            "powerpoint",
            "impress",
        ]
    ):
        return "presentation"

    if any(
        x in title_lower
        for x in [
            "vlc",
            "media player",
        ]
    ):
        return "media_player"

    return "default"


def get_cpu_usage() -> float:
    """Return current CPU usage."""

    return psutil.cpu_percent(
        interval=0.1
    )


def get_ram_usage() -> float:
    """Return current RAM usage percentage."""

    return psutil.virtual_memory().percent


def load_telemetry() -> Dict[str, Any]:
    """
    Load runtime telemetry.

    The file is optional. When interaction modules begin
    publishing telemetry, the dashboard automatically reads it.
    """

    if not TELEMETRY_FILE.exists():

        return {}

    try:

        with TELEMETRY_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        if isinstance(data, dict):
            return data

    except Exception:
        pass

    return {}


def write_demo_telemetry() -> None:
    """
    Create an initial telemetry file when one does not exist.

    This makes the dashboard usable immediately without
    pretending that the values are actual measured results.
    """

    if TELEMETRY_FILE.exists():
        return

    data = {
        "mode": "Idle",
        "fps": None,
        "latency_ms": None,
        "gesture": "None",
        "gesture_counts": {},
        "gesture_accuracy": {},
        "inference_ms": None,
        "updated_at": time.time(),
    }

    try:

        with TELEMETRY_FILE.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                data,
                file,
                indent=2,
            )

    except Exception:
        pass


# ============================================================
# INITIALIZATION
# ============================================================

write_demo_telemetry()

telemetry = load_telemetry()

active_window = get_active_window()
context = detect_context(
    active_window
)

cpu_usage = get_cpu_usage()
ram_usage = get_ram_usage()

fps = telemetry.get(
    "fps"
)

latency_ms = telemetry.get(
    "latency_ms"
)

current_mode = telemetry.get(
    "mode",
    "Idle",
)

current_gesture = telemetry.get(
    "gesture",
    "None",
)

inference_ms = telemetry.get(
    "inference_ms"
)

gesture_counts = telemetry.get(
    "gesture_counts",
    {},
)

gesture_accuracy = telemetry.get(
    "gesture_accuracy",
    {},
)


# ============================================================
# TITLE
# ============================================================

st.title(
    "🖐️ Multimodal Touchless HCI Engine"
)

st.caption(
    "Real-Time Performance Monitoring Dashboard"
)


# ============================================================
# TOP STATUS
# ============================================================

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "Current Mode",
        current_mode,
    )

with col2:

    st.metric(
        "Application",
        context.upper(),
    )

with col3:

    st.metric(
        "CPU Usage",
        f"{cpu_usage:.1f}%",
    )

with col4:

    st.metric(
        "RAM Usage",
        f"{ram_usage:.1f}%",
    )


# ============================================================
# APPLICATION INFORMATION
# ============================================================

st.subheader(
    "Application Context"
)

context_col1, context_col2 = st.columns(2)

with context_col1:

    st.write(
        "**Active Window:**"
    )

    st.code(
        active_window,
        language=None,
    )

with context_col2:

    st.write(
        "**Detected Context:**"
    )

    st.success(
        context.upper()
    )


# ============================================================
# PERFORMANCE
# ============================================================

st.subheader(
    "Real-Time Performance"
)

perf1, perf2, perf3 = st.columns(3)

with perf1:

    if fps is None:

        st.metric(
            "FPS",
            "N/A",
        )

    else:

        fps_value = safe_number(
            fps
        )

        st.metric(
            "FPS",
            f"{fps_value:.1f}",
            delta=(
                f"Target {TARGET_FPS:.0f}"
            ),
        )

with perf2:

    if latency_ms is None:

        st.metric(
            "Latency",
            "N/A",
        )

    else:

        latency_value = safe_number(
            latency_ms
        )

        st.metric(
            "Latency",
            f"{latency_value:.1f} ms",
            delta=(
                f"Target < {TARGET_LATENCY_MS:.0f} ms"
            ),
        )

with perf3:

    if inference_ms is None:

        st.metric(
            "Inference Time",
            "N/A",
        )

    else:

        inference_value = safe_number(
            inference_ms
        )

        st.metric(
            "Inference Time",
            f"{inference_value:.1f} ms",
        )


# ============================================================
# CURRENT GESTURE
# ============================================================

st.subheader(
    "Current Gesture"
)

gesture_col1, gesture_col2 = st.columns(2)

with gesture_col1:

    st.info(
        f"Current Gesture: "
        f"**{current_gesture}**"
    )

with gesture_col2:

    if telemetry.get(
        "updated_at"
    ):

        age = (
            time.time()
            - safe_number(
                telemetry.get(
                    "updated_at"
                )
            )
        )

        st.write(
            f"Telemetry age: "
            f"{age:.1f} seconds"
        )

    else:

        st.write(
            "Telemetry: waiting"
        )


# ============================================================
# GESTURE USAGE
# ============================================================

st.subheader(
    "Gesture Usage"
)

if gesture_counts:

    import pandas as pd

    usage_data = []

    for gesture_name, count in (
        gesture_counts.items()
    ):

        usage_data.append(
            {
                "Gesture": gesture_name,
                "Count": int(
                    safe_number(
                        count
                    )
                ),
            }
        )

    usage_df = pd.DataFrame(
        usage_data
    )

    st.bar_chart(
        usage_df.set_index(
            "Gesture"
        )
    )

else:

    st.info(
        "Gesture usage telemetry is not available yet."
    )


# ============================================================
# GESTURE ACCURACY
# ============================================================

st.subheader(
    "Gesture Accuracy"
)

if gesture_accuracy:

    import pandas as pd

    accuracy_data = []

    for gesture_name, accuracy in (
        gesture_accuracy.items()
    ):

        accuracy_data.append(
            {
                "Gesture": gesture_name,
                "Accuracy (%)": safe_number(
                    accuracy
                ),
            }
        )

    accuracy_df = pd.DataFrame(
        accuracy_data
    )

    st.dataframe(
        accuracy_df,
        use_container_width=True,
    )

else:

    st.warning(
        "Accuracy is not currently measured from a "
        "ground-truth test dataset. "
        "The dashboard will display measured values "
        "once evaluation telemetry is connected."
    )


# ============================================================
# SYSTEM INFORMATION
# ============================================================

st.subheader(
    "System Information"
)

system_col1, system_col2 = st.columns(2)

with system_col1:

    st.write(
        "**Operating System:**",
        platform.system(),
        platform.release(),
    )

    st.write(
        "**Processor:**",
        platform.processor()
        or "Unknown",
    )

with system_col2:

    memory = psutil.virtual_memory()

    st.write(
        "**Total RAM:**",
        f"{memory.total / (1024 ** 3):.2f} GB",
    )

    st.write(
        "**Available RAM:**",
        f"{memory.available / (1024 ** 3):.2f} GB",
    )


# ============================================================
# PROJECT TARGETS
# ============================================================

st.subheader(
    "Project Performance Targets"
)

target_col1, target_col2, target_col3 = st.columns(3)

with target_col1:

    st.metric(
        "Minimum FPS Target",
        "30 FPS",
    )

with target_col2:

    st.metric(
        "Latency Target",
        "< 30 ms",
    )

with target_col3:

    st.metric(
        "Hand Accuracy Target",
        "≥ 95%",
    )


# ============================================================
# REFRESH
# ============================================================

st.caption(
    f"Dashboard refresh interval: "
    f"{REFRESH_SECONDS:.0f} second"
)

time.sleep(
    REFRESH_SECONDS
)

st.rerun()