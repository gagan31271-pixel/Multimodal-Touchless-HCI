import re
import threading
import time
from collections import deque
from typing import Optional, Callable

import numpy as np
import pyautogui
import sounddevice as sd
import whisper


class DictationEngine:
    """
    Whisper-based continuous voice typing.

    The engine records one bounded speech segment at a time.
    After transcription:
        - control phrase -> execute control
        - normal speech  -> type into active application

    Primary stop command:
        "stop typing"
    """

    SAMPLE_RATE = 16000
    CHANNELS = 1
    BLOCK_DURATION = 0.10

    def __init__(
        self,
        model_name="base",
        max_segment_seconds=8.0,
        silence_seconds=0.9,
        minimum_speech_seconds=0.35,
        threshold_multiplier=2.2,
        minimum_threshold=0.008,
        typing_interval=0.01,
        on_status: Optional[Callable[[str], None]] = None,
        on_stop: Optional[Callable[[], None]] = None,
    ):
        self.model_name = model_name

        self.max_segment_seconds = max_segment_seconds
        self.silence_seconds = silence_seconds
        self.minimum_speech_seconds = minimum_speech_seconds

        self.threshold_multiplier = threshold_multiplier
        self.minimum_threshold = minimum_threshold

        self.typing_interval = typing_interval

        self.on_status = on_status
        self.on_stop = on_stop

        self.model = None

        self.running = False
        self.paused = False

        self.stop_event = threading.Event()
        self.thread = None

        self.history = deque(maxlen=10)

    # =========================================================
    # STATUS
    # =========================================================

    def status(self, message):
        print(f"[DICTATION] {message}")

        if self.on_status:
            try:
                self.on_status(message)
            except Exception:
                pass

    # =========================================================
    # LOAD WHISPER
    # =========================================================

    def load_model(self):
        if self.model is not None:
            return

        self.status(
            f"Loading Whisper '{self.model_name}'..."
        )

        self.model = whisper.load_model(
            self.model_name
        )

        self.status(
            "Whisper model loaded."
        )

    # =========================================================
    # AUDIO LEVEL
    # =========================================================

    @staticmethod
    def rms(audio):
        audio = np.asarray(
            audio,
            dtype=np.float32,
        )

        if audio.size == 0:
            return 0.0

        return float(
            np.sqrt(
                np.mean(
                    np.square(audio)
                )
            )
        )

    # =========================================================
    # MICROPHONE CALIBRATION
    # =========================================================

    def calibrate_noise(self):
        self.status(
            "Calibrating microphone..."
        )

        try:
            audio = sd.rec(
                int(
                    0.6 * self.SAMPLE_RATE
                ),
                samplerate=self.SAMPLE_RATE,
                channels=self.CHANNELS,
                dtype="float32",
            )

            sd.wait()

            level = self.rms(
                audio[:, 0]
            )

            threshold = max(
                self.minimum_threshold,
                level * self.threshold_multiplier,
            )

            self.status(
                f"Speech threshold: {threshold:.5f}"
            )

            return threshold

        except Exception as exc:
            self.status(
                f"Calibration failed: {exc}"
            )

            return self.minimum_threshold

    # =========================================================
    # RECORD ONE SEGMENT
    # =========================================================

    def record_one_segment(self):

        block_size = int(
            self.SAMPLE_RATE
            * self.BLOCK_DURATION
        )

        threshold = self.calibrate_noise()

        frames = []

        speech_started = False
        silence_time = 0.0
        total_time = 0.0
        speech_time = 0.0

        pre_roll = deque(
            maxlen=4
        )

        self.status(
            "Listening..."
        )

        try:
            with sd.InputStream(
                samplerate=self.SAMPLE_RATE,
                channels=self.CHANNELS,
                dtype="float32",
                blocksize=block_size,
            ) as stream:

                while not self.stop_event.is_set():

                    data, overflowed = stream.read(
                        block_size
                    )

                    if overflowed:
                        self.status(
                            "Audio buffer overflow."
                        )

                    audio = data[:, 0].copy()

                    level = self.rms(audio)

                    pre_roll.append(audio)

                    total_time += self.BLOCK_DURATION

                    # -----------------------------------------
                    # Waiting for speech
                    # -----------------------------------------

                    if not speech_started:

                        if level >= threshold:

                            speech_started = True

                            frames.extend(
                                list(pre_roll)
                            )

                            speech_time = (
                                len(frames)
                                * self.BLOCK_DURATION
                            )

                            silence_time = 0.0

                            self.status(
                                "Speech detected."
                            )

                        elif total_time >= 5.0:

                            return None

                    # -----------------------------------------
                    # Speech detected
                    # -----------------------------------------

                    else:

                        frames.append(audio)

                        speech_time += (
                            self.BLOCK_DURATION
                        )

                        if level >= threshold:

                            silence_time = 0.0

                        else:

                            silence_time += (
                                self.BLOCK_DURATION
                            )

                        if (
                            speech_time
                            >= self.minimum_speech_seconds
                            and silence_time
                            >= self.silence_seconds
                        ):
                            break

                    # -----------------------------------------
                    # Safety limit
                    # -----------------------------------------

                    if (
                        total_time
                        >= self.max_segment_seconds
                    ):
                        self.status(
                            "Maximum speech segment reached."
                        )
                        break

        except Exception as exc:

            self.status(
                f"Recording error: {exc}"
            )

            return None

        if self.stop_event.is_set():
            return None

        if not frames:
            return None

        return np.concatenate(frames)

    # =========================================================
    # TRANSCRIPTION
    # =========================================================

    def transcribe(self, audio):

        try:

            result = self.model.transcribe(
                audio,
                language="en",
                fp16=False,
                temperature=0,
                condition_on_previous_text=False,
                verbose=False,
            )

            return result.get(
                "text",
                ""
            ).strip()

        except Exception as exc:

            self.status(
                f"Whisper error: {exc}"
            )

            return ""

    # =========================================================
    # CONTROL COMMAND
    # =========================================================

    @staticmethod
    def get_control_command(text):

        normalized = text.lower().strip()

        normalized = re.sub(
            r"[.!?,]+$",
            "",
            normalized,
        )

        normalized = re.sub(
            r"\s+",
            " ",
            normalized,
        )

        # -----------------------------------------
        # STOP TYPING
        # -----------------------------------------

        stop_patterns = (
            "stop typing",
            "please stop typing",
            "stop the typing",
            "stop typing now",
            "stop writing",
            "stop dictation",
        )

        for pattern in stop_patterns:

            if normalized == pattern:
                return "stop"

            if normalized.startswith(
                pattern + " "
            ):
                return "stop"

        # -----------------------------------------
        # PAUSE
        # -----------------------------------------

        pause_patterns = (
            "pause typing",
            "pause dictation",
            "pause the typing",
        )

        for pattern in pause_patterns:

            if normalized == pattern:
                return "pause"

        # -----------------------------------------
        # RESUME
        # -----------------------------------------

        resume_patterns = (
            "resume typing",
            "resume dictation",
            "continue typing",
            "continue dictation",
        )

        for pattern in resume_patterns:

            if normalized == pattern:
                return "resume"

        # -----------------------------------------
        # NEW LINE
        # -----------------------------------------

        if normalized in {
            "new line",
            "next line",
        }:
            return "newline"

        # -----------------------------------------
        # NEW PARAGRAPH
        # -----------------------------------------

        if normalized == "new paragraph":
            return "paragraph"

        # -----------------------------------------
        # DELETE
        # -----------------------------------------

        if normalized in {
            "delete that",
            "delete previous",
            "remove that",
        }:
            return "delete"

        return None

    # =========================================================
    # TYPE NORMAL TEXT
    # =========================================================

    def type_text(self, text):

        if not text:
            return

        self.status(
            f"Typing: {text}"
        )

        pyautogui.write(
            text,
            interval=self.typing_interval,
        )

        # Complete the current dictated line.
        pyautogui.press("enter")

        self.history.append(text)

    # =========================================================
    # DELETE PREVIOUS
    # =========================================================

    def delete_previous(self):

        if not self.history:
            self.status(
                "Nothing to delete."
            )
            return

        previous = self.history.pop()

        pyautogui.hotkey(
            "ctrl",
            "z",
        )

        self.status(
            f"Deleted: {previous}"
        )

    # =========================================================
    # HANDLE TRANSCRIPT
    # =========================================================

    def handle_transcript(self, text):

        if not text:
            return

        self.status(
            f"Recognized: {text}"
        )

        command = self.get_control_command(
            text
        )

        # -----------------------------------------
        # STOP
        # -----------------------------------------

        if command == "stop":

            self.status(
                "STOP TYPING command detected."
            )

            self.stop()

            return

        # -----------------------------------------
        # PAUSE
        # -----------------------------------------

        if command == "pause":

            self.pause()

            return

        # -----------------------------------------
        # RESUME
        # -----------------------------------------

        if command == "resume":

            self.resume()

            return

        # -----------------------------------------
        # NEW LINE
        # -----------------------------------------

        if command == "newline":

            pyautogui.press("enter")

            return

        # -----------------------------------------
        # NEW PARAGRAPH
        # -----------------------------------------

        if command == "paragraph":

            pyautogui.press("enter")
            pyautogui.press("enter")

            return

        # -----------------------------------------
        # DELETE
        # -----------------------------------------

        if command == "delete":

            self.delete_previous()

            return

        # -----------------------------------------
        # NORMAL SPEECH
        # -----------------------------------------

        self.type_text(
            text
        )

    # =========================================================
    # WORKER
    # =========================================================

    def worker(self):

        try:

            self.load_model()

            self.status(
                "Dictation mode ready."
            )

            while not self.stop_event.is_set():

                if self.paused:

                    time.sleep(0.1)
                    continue

                audio = self.record_one_segment()

                if audio is None:
                    continue

                if self.stop_event.is_set():
                    break

                self.status(
                    "Transcribing..."
                )

                text = self.transcribe(
                    audio
                )

                if text:
                    self.handle_transcript(
                        text
                    )

        except Exception as exc:

            self.status(
                f"Dictation worker error: {exc}"
            )

        finally:

            self.running = False

            self.status(
                "Dictation mode stopped."
            )

            if self.on_stop:

                try:
                    self.on_stop()

                except Exception:
                    pass

    # =========================================================
    # START
    # =========================================================

    def start(self):

        if self.running:

            self.status(
                "Dictation is already running."
            )

            return False

        self.stop_event.clear()

        self.paused = False
        self.running = True

        self.thread = threading.Thread(
            target=self.worker,
            daemon=True,
        )

        self.thread.start()

        return True

    # =========================================================
    # STOP
    # =========================================================

    def stop(self):

        if not self.running:
            return

        self.stop_event.set()
        self.paused = False

        self.status(
            "Stopping dictation..."
        )

    # =========================================================
    # PAUSE
    # =========================================================

    def pause(self):

        if not self.running:
            return

        self.paused = True

        self.status(
            "Dictation paused."
        )

    # =========================================================
    # RESUME
    # =========================================================

    def resume(self):

        if not self.running:
            return

        self.paused = False

        self.status(
            "Dictation resumed."
        )

    # =========================================================
    # WAIT
    # =========================================================

    def wait(self):

        if self.thread is not None:
            self.thread.join()