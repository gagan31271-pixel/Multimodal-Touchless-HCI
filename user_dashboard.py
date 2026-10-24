"""Unified Streamlit dashboard for Multimodal Touchless HCI.

Hand and Eye share one browser-owned WebRTC camera stream. MAX remains an
independent voice process. Screen AI is a separate shared feature and does not
stop whichever interaction mode is active.
"""

from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
from types import SimpleNamespace
from pathlib import Path

import cv2
import streamlit as st
from streamlit_webrtc import VideoProcessorBase, WebRtcMode, webrtc_streamer
from modules.security.face_lock import render_face_lock


ROOT = Path(__file__).resolve().parent
METRICS_FILE = ROOT / "runtime_metrics.json"
CAMERA_MODES = {"Hand Gesture", "Eye / Wink"}
ALL_MODES = ["Hand Gesture", "Eye / Wink", "MAX / Voice"]


def load_metrics() -> dict:
    try:
        with METRICS_FILE.open("r", encoding="utf-8") as file:
            value = json.load(file)
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


class DashboardVideoProcessor(VideoProcessorBase):
    """Single WebRTC frame processor; creates only the selected mode engine."""

    def __init__(self, mode: str | None = None):
        self._lock = threading.RLock()
        self.mode = None
        self.engine = None
        self.context_manager = None
        self.last = {
            "gesture": "None",
            "action": "None",
            "hand": "None",
            "wink": "None",
            "eye_status": "Waiting",
            "context": "default",
            "application": "",
            "mapping": {},
            "fps": 0.0,
            "latency_ms": 0.0,
            "inference_ms": 0.0,
            "error": "",
        }
        self._frame_times: list[float] = []
        self._last_custom_action = None
        self._last_custom_action_time = 0.0

        if mode:
            self.set_mode(mode)

    def set_mode(self, mode: str | None) -> None:
        if mode not in CAMERA_MODES:
            mode = None

        with self._lock:
            if self.mode == mode:
                return

            self._close_engine()
            self.mode = mode
            self.last["error"] = ""

            if mode is None:
                self.last.update(
                    gesture="None",
                    action="None",
                    hand="None",
                    wink="None",
                    eye_status="Stopped",
                )
                return

            try:
                if mode == "Hand Gesture":
                    from modules.hand_gesture.hand_mouse import HandGestureMouse

                    self.engine = HandGestureMouse(show_window=False)
                else:
                    from modules.multimodal.eye_mode import EyeMode

                    self.engine = EyeMode()

                from modules.context_switcher.context_manager import ContextManager

                self.context_manager = ContextManager(check_interval=2.0)
                self.context_manager.start()

            except Exception as exc:
                self.last["error"] = f"Could not start {mode}: {exc}"
                self._close_engine()
                self.mode = None

    def _close_engine(self) -> None:
        if self.context_manager is not None:
            try:
                self.context_manager.stop()
            except Exception:
                pass

            self.context_manager = None

        if self.engine is not None:
            try:
                self.engine.stop()
            except Exception:
                try:
                    self.engine.detector.close()
                except Exception:
                    pass

                try:
                    self.engine.face_detector.close()
                except Exception:
                    pass

            self.engine = None

    def recv(self, frame):
        started = time.perf_counter()
        image = frame.to_ndarray(format="bgr24")

        with self._lock:
            if self.mode and self.engine is not None:
                try:
                    if self.mode == "Hand Gesture":
                        result = self.engine.process_frame(
                            image,
                            execute_action=False,
                            draw_landmarks=True,
                        )

                        action = self._apply_hand_context_action()

                        self.last.update(
                            gesture=result.get("gesture", "None"),
                            action=action or result.get("action", "None"),
                            hand=result.get("hand", "None"),
                        )

                        image = result.get("frame", image)

                    else:
                        result = self.engine.process_frame(image)
                        image = result.get("frame", image)

                        self.last.update(
                            wink=result.get("wink", "NONE").replace("_", " ").title(),
                            action=result.get("action", "None"),
                            eye_status=result.get("eye_status", "No face"),
                        )

                    if self.context_manager is not None:
                        context = self.context_manager.get_context()

                        self.last.update(
                            context=context.get("profile_name", "default"),
                            application=context.get("application") or "",
                            mapping=context.get("gesture_mapping") or {},
                        )

                    self.last["error"] = ""

                except Exception as exc:
                    self.last["error"] = f"Frame processing error: {exc}"

            now = time.perf_counter()
            self._frame_times.append(now)
            self._frame_times = [
                t for t in self._frame_times if now - t < 2.0
            ]

            self.last["fps"] = (
                len(self._frame_times)
                / max(0.1, now - self._frame_times[0])
                if len(self._frame_times) > 1
                else 0.0
            )

            elapsed = (now - started) * 1000
            self.last["latency_ms"] = elapsed
            self.last["inference_ms"] = elapsed

        return type(frame).from_ndarray(image, format="bgr24")

    def _apply_hand_context_action(self) -> str | None:
        """Dispatch YAML context actions; default actions retain controller logic."""
        from modules.hand_gesture.gesture_classifier import Gesture
        import pyautogui

        gesture = self.engine.current_gesture

        mapping_key = {
            Gesture.INDEX_ONLY: "index_only",
            Gesture.TWO_FINGER: "index_middle",
            Gesture.THREE_FINGER: "index_middle_ring",
            Gesture.INDEX_LITTLE: "index_little",
            Gesture.THUMB_UP: "thumb_only",
            Gesture.THUMB_LITTLE: "thumb_little",
            Gesture.FIST: "fist",
        }.get(gesture)

        mapped = None

        if mapping_key and self.context_manager is not None:
            mapped = self.context_manager.get_gesture_mapping(mapping_key)

        if not mapped:
            self.engine.controller.handle_gesture(
                gesture,
                SimpleNamespace(landmark=self._selected_hand_landmarks()),
            )
            self._last_custom_action = None
            return None

        action = str(mapped).strip().lower()
        landmarks = self._selected_hand_landmarks()
        controller = self.engine.controller

        if gesture != Gesture.INDEX_LITTLE:
            controller.stop_drag()

        if action == "cursor":
            if landmarks is not None:
                controller.move_from_landmark(landmarks[8])

            self._last_custom_action = None
            return "Cursor movement"

        if action == "left_click":
            controller.left_click()

        elif action == "right_click":
            controller.right_click()

        elif action == "drag":
            if landmarks is not None:
                controller.move_from_landmark(landmarks[8])

            controller.start_drag()

        elif action == "scroll_up":
            controller.scroll_up()

        elif action == "scroll_down":
            controller.scroll_down()

        elif action in {"neutral", "none"}:
            controller.stop_drag()

        else:
            key_actions = {
                "next_slide": ("right", "Next slide"),
                "previous_slide": ("left", "Previous slide"),
                "play_pause": ("space", "Play / pause"),
                "mute": ("m", "Mute"),
                "volume_up": ("volumeup", "Volume up"),
                "volume_down": ("volumedown", "Volume down"),
            }

            key_action = key_actions.get(action)

            if key_action is None:
                controller.handle_gesture(
                    gesture,
                    SimpleNamespace(landmark=landmarks),
                )
                self._last_custom_action = None
                return None

            now = time.monotonic()
            signature = (gesture, action)

            if (
                signature != self._last_custom_action
                or now - self._last_custom_action_time >= 0.55
            ):
                pyautogui.press(key_action[0])
                self._last_custom_action_time = now

            self._last_custom_action = signature
            return key_action[1]

        self._last_custom_action = None

        return {
            "left_click": "Left click",
            "right_click": "Right click",
            "drag": "Drag",
            "scroll_up": "Scroll up",
            "scroll_down": "Scroll down",
            "neutral": "Neutral",
            "none": "Neutral",
        }.get(action, action.replace("_", " ").title())

    def _selected_hand_landmarks(self):
        hands = getattr(self.engine, "last_detected_hands", [])

        if not hands:
            return None

        hand = self.engine.detector.get_primary_hand(
            hands,
            preferred_label=self.engine.preferred_hand,
        )

        if hand is None:
            return None

        landmarks = getattr(hand, "landmarks", None)

        # HandDetector stores MediaPipe's NormalizedLandmarkList here.
        # Cursor actions need its indexable .landmark sequence.
        return getattr(landmarks, "landmark", landmarks)

    def snapshot(self) -> dict:
        with self._lock:
            return dict(self.last, mode=self.mode)

    def on_ended(self):
        with self._lock:
            self._close_engine()
            self.mode = None


class VoiceController:
    """Owns the optional MAX process and drains its output safely."""

    def __init__(self):
        self.process = None
        self.reader = None
        self.lines: list[str] = []
        self._lock = threading.Lock()

    def start(self) -> None:
        self.stop()

        runner = ROOT / "mode_runner.py"

        self.process = subprocess.Popen(
            [sys.executable, str(runner), "max"],
            cwd=str(ROOT),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _read(self):
        process = self.process

        if process is None or process.stdout is None:
            return

        for line in process.stdout:
            with self._lock:
                self.lines.append(line.rstrip())
                self.lines = self.lines[-200:]

    def stop(self):
        process = self.process
        self.process = None

        if process is not None:
            if process.poll() is None:
                process.terminate()

                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=2)

            if process.stdout:
                process.stdout.close()

    def output(self):
        with self._lock:
            return list(self.lines)


def stop_camera_processor(ctx) -> None:
    processor = getattr(ctx, "video_processor", None) if ctx else None

    if processor is not None:
        processor.set_mode(None)


# ============================================================
# STREAMLIT PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Multimodal Touchless HCI",
    page_icon="🖐️",
    layout="wide",
)


# ============================================================
# FACE LOCK — AUTHENTICATION GATE
# ============================================================
# This must run before any dashboard interface or interaction mode.

if "face_authenticated" not in st.session_state:
    st.session_state.face_authenticated = False

render_face_lock()


# ============================================================
# DASHBOARD HEADER
# ============================================================

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.5rem;
        max-width: 1400px;
    }

    .hero {
        padding: 1.2rem 1.5rem;
        border-radius: 18px;
        background: linear-gradient(120deg, #10233f, #176c83);
        color: #fff;
    }

    .hero h1 {
        margin: 0;
        font-size: 2rem;
    }

    .hero p {
        margin: .45rem 0 0;
        opacity: .86;
    }

    [data-testid="stMetric"] {
        background: #f4f7fb;
        padding: 12px 16px;
        border-radius: 12px;
    }
    </style>

    <div class="hero">
        <h1>Multimodal Touchless HCI</h1>
        <p>Your hand, eye, voice and screen tools in one place.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

if "active_mode" not in st.session_state:
    st.session_state.active_mode = None

if "selected_mode" not in st.session_state:
    st.session_state.selected_mode = ALL_MODES[0]

if "voice_controller" not in st.session_state:
    st.session_state.voice_controller = VoiceController()

if "screen_output" not in st.session_state:
    st.session_state.screen_output = ""


# ============================================================
# MODE MANAGEMENT
# ============================================================

def stop_active(ctx=None):
    stop_camera_processor(ctx)
    st.session_state.voice_controller.stop()
    st.session_state.active_mode = None


def start_mode(mode: str, ctx=None):
    stop_active(ctx)
    st.session_state.selected_mode = mode

    if mode in CAMERA_MODES:
        st.session_state.active_mode = mode

    elif mode == "MAX / Voice":
        try:
            st.session_state.voice_controller.start()
            st.session_state.active_mode = mode
        except Exception as exc:
            st.error(f"Could not start MAX: {exc}")

    else:
        st.session_state.active_mode = mode


# ============================================================
# MODE SELECTION
# ============================================================

st.subheader("Choose a mode")

cols = st.columns(3)

for column, mode, icon in zip(
    cols,
    ALL_MODES,
    ["🖐️", "👁️", "🎙️"],
):
    with column:
        if st.button(
            f"{icon} {mode}",
            key=f"start_{mode}",
            use_container_width=True,
            type=(
                "primary"
                if st.session_state.active_mode == mode
                else "secondary"
            ),
        ):
            start_mode(mode)

# ============================================================
# ACTIVE MODE STATUS
# ============================================================

active = st.session_state.active_mode
selected = st.session_state.selected_mode

left, right = st.columns([3, 1])

with left:
    st.info(f"Active mode: **{active or 'Stopped'}**")

with right:
    if st.button(
        "■ Stop current mode",
        use_container_width=True,
        disabled=active is None,
    ):
        st.session_state.active_mode = None
        st.session_state.voice_controller.stop()
        st.rerun()


# ============================================================
# SHARED CAMERA STREAM
# ============================================================

camera_active = active in CAMERA_MODES

ctx = webrtc_streamer(
    key="hci-single-camera",
    video_processor_factory=lambda: DashboardVideoProcessor(
        active if camera_active else None
    ),
    media_stream_constraints={"video": True, "audio": False},
    mode=WebRtcMode.SENDONLY,
    desired_playing_state=camera_active,
    async_processing=True,
    sendback_audio=False,
    video_html_attrs={"autoPlay": True, "controls": False},
)

processor = getattr(ctx, "video_processor", None)

if processor is not None:
    processor.set_mode(active if camera_active else None)

camera = processor.snapshot() if processor is not None else {}

if camera.get("error"):
    st.error(camera["error"])


# ============================================================
# HAND GESTURE INTERFACE
# ============================================================

if active == "Hand Gesture":
    st.subheader("Hand Gesture")

    a, b, c = st.columns(3)

    a.metric("Gesture", camera.get("gesture", "Waiting"))
    b.metric("Action", camera.get("action", "Waiting"))
    c.metric("Detected hand", camera.get("hand", "Waiting"))

    st.write(
        f"**Application context:** "
        f"{camera.get('context', 'default')} · "
        f"{camera.get('application') or 'Waiting for active window'}"
    )

    mapping = camera.get("mapping", {})

    with st.expander("Current context gesture mapping", expanded=False):
        st.json(mapping)

    st.caption(
        "The existing hand detector, classifier, cursor actions "
        "and YAML context profiles are used as-is."
    )


# ============================================================
# EYE / WINK INTERFACE
# ============================================================

elif active == "Eye / Wink":
    st.subheader("Eye / Wink")

    a, b = st.columns(2)

    a.metric("Eye status", camera.get("eye_status", "Waiting"))
    b.metric("Last wink / action", camera.get("action", "Waiting"))

    st.caption(
        "Left wink clicks left; right wink clicks right. "
        "A normal two-eye blink is ignored."
    )


# ============================================================
# MAX / VOICE INTERFACE
# ============================================================

elif active == "MAX / Voice":
    st.subheader("MAX conversation")

    st.caption(
        "Voice commands and MAX responses appear here "
        "while the voice mode is running."
    )

    for line in st.session_state.voice_controller.output()[-30:]:
        if "You:" in line or "MAX:" in line:
            st.markdown(line)
        else:
            st.caption(line)


# ============================================================
# SCREEN AI INTERFACE
# ============================================================

# Screen AI is a common feature and remains visible with any active mode.
st.subheader("Screen AI · Common Feature")
st.caption(
    "Screen AI runs independently and can be used while Hand Gesture, "
    "Eye / Wink, or MAX / Voice is active."
)

st.write(
    "Select a screen region first. The Read, Summarize, and Translate "
    "actions will use only the text extracted from that selection."
)

# Keep selected OCR text between Streamlit reruns.
if "selected_screen_text" not in st.session_state:
    st.session_state.selected_screen_text = ""

if "screen_output" not in st.session_state:
    st.session_state.screen_output = ""

if "screen_operation_status" not in st.session_state:
    st.session_state.screen_operation_status = "Ready — select a region to begin."
if "screen_operation_error" not in st.session_state:
    st.session_state.screen_operation_error = False

# --------------------------------------------------------
# SELECT SCREEN REGION
# --------------------------------------------------------

if st.button(
    "🎯 Select Screen Region",
    use_container_width=True,
    type="primary",
):
    service = None

    try:
        from modules.multimodal.screen_service import ScreenService

        service = ScreenService()
        selected_text_result = service.select_text()

        # select_text() can return OCR text or a dictionary.
        if isinstance(selected_text_result, dict):
            selected_text = str(
                selected_text_result.get("text", "") or ""
            )
        else:
            selected_text = str(selected_text_result or "")

        if selected_text.strip():
            selected_text = selected_text.strip()

            st.session_state.selected_screen_text = selected_text
            st.session_state["screen_selected_text_preview"] = selected_text
            st.session_state.screen_output = ""
            st.session_state.screen_operation_status = (
                "Text extracted successfully. Choose Read, Summarize, or Translate."
            )
            st.session_state.screen_operation_error = False

            st.success("Screen region selected and text extracted.")

        else:
            st.session_state.selected_screen_text = ""
            st.session_state["screen_selected_text_preview"] = ""
            st.session_state.screen_output = ""
            st.session_state.screen_operation_status = (
                "No text detected. Select a region containing readable text."
            )
            st.session_state.screen_operation_error = True

            st.warning(
                "No text was detected in that region. "
                "Please select a region containing readable text."
            )

    except Exception as exc:
        st.session_state.selected_screen_text = ""
        st.session_state["screen_selected_text_preview"] = ""
        st.session_state.screen_operation_status = f"Screen selection failed: {exc}"
        st.session_state.screen_operation_error = True

        st.error(f"Screen selection error: {exc}")

    finally:
        if service is not None:
            try:
                service.close()
            except Exception:
                pass

# --------------------------------------------------------
# DISPLAY EXTRACTED TEXT
# --------------------------------------------------------

if st.session_state.selected_screen_text:
    st.markdown("**Extracted text from your selected region**")

    st.text_area(
        "Selected text preview",
        value=st.session_state.selected_screen_text,
        height=150,
        disabled=True,
        key="screen_selected_text_preview",
    )

    st.caption(
        "Choose an action to process this exact extracted text. "
        "Select another region any time to replace it."
    )

    c1, c2, c3 = st.columns(3)

    actions = [
        (c1, "📖 Read", "read"),
        (c2, "📝 Summarize", "summarize"),
        (c3, "🌐 Translate to Kannada", "translate"),
    ]

    # ----------------------------------------------------
    # READ / SUMMARIZE / TRANSLATE
    # ----------------------------------------------------

    for column, label, operation in actions:
        with column:
            if st.button(
                label,
                use_container_width=True,
                key=f"screen_action_{operation}",
            ):
                service = None

                try:
                    from modules.multimodal.screen_service import ScreenService

                    service = ScreenService()

                    kwargs = {
                        "text": st.session_state.selected_screen_text,
                        "operation": operation,
                        "speak": True,
                    }

                    if operation == "translate":
                        kwargs["target_language"] = "Kannada"

                    result = service.processor.process_text(**kwargs)

                    # Extract readable text from the returned result.
                    if isinstance(result, dict):
                        preferred_keys = {
                            "read": (
                                "message",
                                "result",
                                "text",
                                "output",
                                "status",
                            ),
                            "summarize": (
                                "summary",
                                "result",
                                "output",
                                "text",
                                "message",
                            ),
                            "translate": (
                                "translation",
                                "translated_text",
                                "result",
                                "output",
                                "text",
                                "message",
                            ),
                        }.get(
                            operation,
                            ("result", "output", "text", "message"),
                        )

                        display_result = ""

                        for key in preferred_keys:
                            value = result.get(key)

                            if isinstance(value, str) and value.strip():
                                display_result = value.strip()
                                break

                        if (
                            not display_result
                            and result.get("success") is False
                        ):
                            display_result = str(
                                result.get("error")
                                or result.get("message")
                                or "The operation failed."
                            )

                        if not display_result and operation == "read":
                            display_result = (
                                "The selected text was sent to speech output."
                            )

                        if not display_result:
                            display_result = (
                                "Operation completed, but no text result "
                                "was returned."
                            )

                    elif isinstance(result, str):
                        display_result = (
                            result.strip()
                            or "Operation completed, but no text result "
                            "was returned."
                        )

                    else:
                        display_result = (
                            "Operation completed, but no text result "
                            "was returned."
                        )

                    st.session_state.screen_output = display_result
                    st.session_state.screen_operation_status = (
                        f"{operation.title()} completed successfully."
                    )
                    st.session_state.screen_operation_error = False

                except Exception as exc:
                    st.session_state.screen_output = ""
                    st.session_state.screen_operation_status = (
                        f"{operation.title()} failed: {exc}"
                    )
                    st.session_state.screen_operation_error = True

                finally:
                    if service is not None:
                        try:
                            service.close()
                        except Exception:
                            pass

    if st.session_state.screen_operation_error:
        st.error(st.session_state.screen_operation_status)
    else:
        st.info(st.session_state.screen_operation_status)

    # Keep the operation result readable even though the text area is disabled.
    st.markdown(
        """
        <style>
        div[data-testid="stTextArea"] textarea:disabled {
            color: #222222 !important;
            -webkit-text-fill-color: #222222 !important;
            opacity: 1 !important;
        }

        /*
         * Streamlit may retain a second, disabled rendering of the action row
         * after a rerun. Hide that whole row, not just its individual buttons.
         * aria-disabled covers Streamlit versions that don't set :disabled.
         */
        div[data-testid="stHorizontalBlock"]:has(button:disabled),
        div[data-testid="stHorizontalBlock"]:has(button[aria-disabled="true"]) {
            display: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.text_area(
        "Operation result",
        key="screen_output",
        height=190,
        disabled=True,
    )

else:
    st.info(
        "Click 'Select Screen Region' to capture a region and extract "
        "its text. Read, Summarize, and Translate will appear after "
        "text is detected."
    )

# ============================================================
# PERFORMANCE DASHBOARD
# ============================================================

st.divider()
st.subheader("Performance")

old_metrics = load_metrics()

if camera_active and camera:
    fps = camera.get("fps", 0.0)
    latency = camera.get("latency_ms", 0.0)
    inference = camera.get("inference_ms", 0.0)

else:
    fps = old_metrics.get("fps", 0.0)
    latency = old_metrics.get("latency_ms", 0.0)
    inference = old_metrics.get("inference_ms", 0.0)

try:
    import psutil

    cpu = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory().percent

except Exception:
    cpu = old_metrics.get("cpu_percent", 0.0)
    ram = old_metrics.get("ram_percent", 0.0)

metrics = st.columns(6)

for col, label, value, suffix in zip(
    metrics,
    ["FPS", "Latency", "Inference", "CPU", "RAM", "Context"],
    [
        fps,
        latency,
        inference,
        cpu,
        ram,
        camera.get("context", old_metrics.get("context", "default")),
    ],
    ["", " ms", " ms", "%", "%", ""],
):
    display = (
        value
        if isinstance(value, str)
        else f"{float(value or 0):.1f}{suffix}"
    )

    col.metric(label, display)


# ============================================================
# GESTURE REFERENCE
# ============================================================

with st.expander("Gesture reference"):
    st.markdown(
        "| Gesture | Default action |\n"
        "|---|---|\n"
        "| Index only | Cursor movement |\n"
        "| Index + middle | Left click |\n"
        "| Index + middle + ring | Right click |\n"
        "| Index + little | Drag |\n"
        "| Thumb only | Scroll up |\n"
        "| Thumb + little | Scroll down |\n"
        "| Fist | Neutral |"
    )


st.caption(
    "Run locally with `streamlit run user_dashboard.py`. "
    "Browser camera access requires localhost or HTTPS."
)

