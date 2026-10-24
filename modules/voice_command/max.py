import datetime
import os
import re
import threading
import time
import webbrowser

import pyautogui
import speech_recognition as sr

from modules.voice_command.application_controller import (
    ApplicationController,
)

from modules.voice_command.dictation_engine import (
    DictationEngine,
)


class MAX:
    """
    MAX - Multimodal Touchless HCI Voice Assistant

    Current capabilities:
        - Date
        - Time
        - Web search
        - Location / Maps
        - File listing
        - File opening by number
        - Go back
        - Copy / Paste
        - Gesture start / stop
        - Application launching
        - Application + typing
        - Browser search
        - Whisper continuous typing
        - Voice "stop typing"
        - Pause / resume typing
        - Close active window
        - Close named application
        - Close browser
        - Sleep / wake
        - Exit
    """

    def __init__(self):

        # =====================================================
        # NORMAL MAX SPEECH RECOGNITION
        # =====================================================

        self.recognizer = sr.Recognizer()

        # Stable Proton-style settings
        self.recognizer.energy_threshold = 500
        self.recognizer.dynamic_energy_threshold = False
        self.recognizer.pause_threshold = 0.8

        self.microphone = sr.Microphone()

        # =====================================================
        # APPLICATION CONTROLLER
        # =====================================================

        self.app_controller = ApplicationController(
            launch_delay=1.2
        )

        # =====================================================
        # DICTATION
        # =====================================================

        self.dictation_engine = None
        self.dictation_active = False

        # =====================================================
        # MAIN STATE
        # =====================================================

        self.running = True
        self.sleeping = False

        # =====================================================
        # GESTURE CONTROLLER
        # =====================================================

        self.gesture_controller = None
        self.gesture_thread = None

        # =====================================================
        # WINDOWS SAPI TTS
        # =====================================================

        self.tts_lock = threading.Lock()

        try:
            import win32com.client

            self.speaker = win32com.client.Dispatch(
                "SAPI.SpVoice"
            )

            self.speaker.Rate = 0
            self.speaker.Volume = 100

            self.tts_available = True

        except Exception as exc:

            self.speaker = None
            self.tts_available = False

            print(
                f"[MAX] Windows SAPI unavailable: {exc}"
            )

    # =========================================================
    # TEXT TO SPEECH
    # =========================================================

    def speak(self, text: str):

        print(f"[MAX] {text}")

        if not self.tts_available:
            return

        try:
            with self.tts_lock:
                self.speaker.Speak(str(text))

        except Exception as exc:
            print(f"[MAX] TTS error: {exc}")

    # =========================================================
    # NORMAL MAX LISTENING
    # =========================================================

    def listen(self):

        try:

            with self.microphone as source:

                print()
                print("[MAX] Listening...")

                audio = self.recognizer.listen(
                    source,
                    timeout=8,
                    phrase_time_limit=6,
                )

            print("[MAX] Processing speech...")

            command = self.recognizer.recognize_google(
                audio
            )

            command = command.strip()

            print(
                f"[MAX] RAW command: {command}"
            )

            return command

        except sr.WaitTimeoutError:

            print("[MAX] Listening timeout.")
            return ""

        except sr.UnknownValueError:

            print(
                "[MAX] Could not understand speech."
            )

            return ""

        except sr.RequestError as exc:

            print(
                f"[MAX] Speech recognition error: {exc}"
            )

            return ""

        except Exception as exc:

            print(
                f"[MAX] Listen error: {exc}"
            )

            return ""

    # =========================================================
    # COMMAND CLEANING
    # =========================================================

    @staticmethod
    def clean_command(command: str) -> str:

        command = (
            command
            .lower()
            .strip()
        )

        # Remove wake word.
        command = re.sub(
            r"^\s*(hey\s+)?max[\s,]*(please\s+)?",
            "",
            command,
            flags=re.IGNORECASE,
        )

        return command.strip()

    # =========================================================
    # WORD MATCHING
    # =========================================================

    @staticmethod
    def contains_any(text: str, words):

        return any(
            word in text
            for word in words
        )

    # =========================================================
    # FIND APPLICATION
    # =========================================================

    def find_application_in_command(
        self,
        command: str,
    ):

        applications = (
            self.app_controller
            .get_supported_applications()
        )

        # Longest application names first.
        applications = sorted(
            applications,
            key=len,
            reverse=True,
        )

        for app_name in applications:

            pattern = (
                r"\b"
                + re.escape(
                    app_name.lower()
                )
                + r"\b"
            )

            if re.search(
                pattern,
                command,
                flags=re.IGNORECASE,
            ):

                return app_name

        return None

    # =========================================================
    # APPLICATION COMMAND HANDLER
    # =========================================================

    def handle_application_command(
        self,
        command: str,
    ) -> bool:

        app_name = (
            self.find_application_in_command(
                command
            )
        )

        if not app_name:
            return False

        print(
            f"[MAX APP] Detected application: "
            f"{app_name}"
        )

        # -----------------------------------------------------
        # OPEN + SEARCH
        # -----------------------------------------------------

        search_patterns = [
            r"(?:open|launch|start)\s+.+?"
            r"\s+(?:and\s+)?search\s+for\s+(.+)$",

            r"(?:open|launch|start)\s+.+?"
            r"\s+(?:and\s+)?search\s+(.+)$",
        ]

        for pattern in search_patterns:

            match = re.search(
                pattern,
                command,
                flags=re.IGNORECASE,
            )

            if not match:
                continue

            query = (
                match.group(1)
                .strip()
            )

            if not self.app_controller.is_browser(
                app_name
            ):

                self.speak(
                    "Search mode is available "
                    "for Chrome and Edge."
                )

                return True

            self.speak(
                f"Opening {app_name} "
                f"and searching for {query}."
            )

            success = (
                self.app_controller
                .open_and_search(
                    app_name,
                    query,
                )
            )

            if not success:

                self.speak(
                    f"I could not open "
                    f"{app_name}."
                )

            return True

        # -----------------------------------------------------
        # OPEN + TYPE
        # -----------------------------------------------------

        type_patterns = [
            r"(?:open|launch|start)\s+.+?"
            r"\s+(?:and\s+)?type\s+(.+)$",

            r"(?:open|launch|start)\s+.+?"
            r"\s+(?:and\s+)?write\s+(.+)$",
        ]

        for pattern in type_patterns:

            match = re.search(
                pattern,
                command,
                flags=re.IGNORECASE,
            )

            if not match:
                continue

            text = (
                match.group(1)
                .strip()
            )

            self.speak(
                f"Opening {app_name} "
                f"and typing the text."
            )

            success = (
                self.app_controller
                .open_and_type(
                    app_name,
                    text,
                )
            )

            if not success:

                self.speak(
                    f"I could not open "
                    f"{app_name}."
                )

            return True

        # -----------------------------------------------------
        # SIMPLE APP OPEN
        # -----------------------------------------------------

        if self.contains_any(
            command,
            [
                "open ",
                "launch ",
                "start ",
            ],
        ):

            self.speak(
                f"Opening {app_name}."
            )

            success = (
                self.app_controller
                .open_application(
                    app_name
                )
            )

            if not success:

                self.speak(
                    f"I could not open "
                    f"{app_name}."
                )

            return True

        return False

    # =========================================================
    # CLOSE CURRENT ACTIVE WINDOW
    # =========================================================

    def close_active_window(self):

        try:

            print(
                "[MAX] Closing active window."
            )

            pyautogui.hotkey(
                "alt",
                "f4",
            )

            time.sleep(0.3)

            self.speak(
                "Closed the current window."
            )

        except Exception as exc:

            print(
                f"[MAX] Close window error: {exc}"
            )

            self.speak(
                "I could not close the current window."
            )

    # =========================================================
    # FIND AND CLOSE NAMED APPLICATION
    # =========================================================

    def close_named_application(
        self,
        app_name: str,
    ):

        app_name = (
            app_name
            .lower()
            .strip()
        )

        print(
            f"[MAX] Requested close: {app_name}"
        )

        # -----------------------------------------------------
        # Import pygetwindow
        # -----------------------------------------------------

        try:

            import pygetwindow as gw

        except ImportError:

            print(
                "[MAX] pygetwindow is not installed."
            )

            self.speak(
                "I cannot locate application windows."
            )

            return

        # -----------------------------------------------------
        # Window title aliases
        # -----------------------------------------------------

        title_keywords = {

            "notepad": [
                "notepad",
            ],

            "calculator": [
                "calculator",
            ],

            "calc": [
                "calculator",
            ],

            "chrome": [
                "chrome",
                "google chrome",
            ],

            "google chrome": [
                "chrome",
                "google chrome",
            ],

            "edge": [
                "edge",
                "microsoft edge",
            ],

            "microsoft edge": [
                "edge",
                "microsoft edge",
            ],

            "browser": [
                "chrome",
                "google chrome",
                "edge",
                "microsoft edge",
            ],

            "web": [
                "chrome",
                "google chrome",
                "edge",
                "microsoft edge",
            ],

            "web search": [
                "chrome",
                "google chrome",
                "edge",
                "microsoft edge",
            ],

            "paint": [
                "paint",
            ],

            "ms paint": [
                "paint",
            ],

            "file explorer": [
                "file explorer",
                "explorer",
            ],

            "explorer": [
                "file explorer",
                "explorer",
            ],

            "command prompt": [
                "command prompt",
                "cmd",
            ],

            "cmd": [
                "command prompt",
                "cmd",
            ],

            "powershell": [
                "powershell",
            ],

            "task manager": [
                "task manager",
            ],

            "settings": [
                "settings",
            ],

            "control panel": [
                "control panel",
            ],

            "visual studio code": [
                "visual studio code",
                "vscode",
            ],

            "vs code": [
                "visual studio code",
                "vscode",
            ],

            "vscode": [
                "visual studio code",
                "vscode",
            ],

            "word": [
                "word",
            ],

            "microsoft word": [
                "word",
            ],

            "excel": [
                "excel",
            ],

            "microsoft excel": [
                "excel",
            ],

            "powerpoint": [
                "powerpoint",
            ],

            "power point": [
                "powerpoint",
            ],

            "outlook": [
                "outlook",
            ],

            "spotify": [
                "spotify",
            ],

            "discord": [
                "discord",
            ],

            "whatsapp": [
                "whatsapp",
            ],

            "steam": [
                "steam",
            ],

            "terminal": [
                "terminal",
                "windows terminal",
            ],

            "windows terminal": [
                "terminal",
                "windows terminal",
            ],

            "snipping tool": [
                "snipping tool",
            ],

            "camera": [
                "camera",
            ],
        }

        keywords = title_keywords.get(
            app_name,
            [app_name],
        )

        # -----------------------------------------------------
        # CHECK ACTIVE WINDOW FIRST
        # -----------------------------------------------------

        try:

            active_window = gw.getActiveWindow()

            if active_window is not None:

                active_title = (
                    active_window.title
                    .strip()
                    .lower()
                )

                print(
                    f"[MAX] Active window: "
                    f"{active_title}"
                )

                for keyword in keywords:

                    if keyword in active_title:

                        try:
                            active_window.activate()
                        except Exception:
                            pass

                        time.sleep(0.3)

                        pyautogui.hotkey(
                            "alt",
                            "f4",
                        )

                        self.speak(
                            f"Closed {app_name}."
                        )

                        return

        except Exception as exc:

            print(
                "[MAX] Active window check failed: "
                f"{exc}"
            )

        # -----------------------------------------------------
        # SEARCH ALL WINDOWS
        # -----------------------------------------------------

        try:

            windows = gw.getAllWindows()

        except Exception as exc:

            print(
                "[MAX] Could not enumerate windows: "
                f"{exc}"
            )

            self.speak(
                f"I could not find {app_name}."
            )

            return

        matched_window = None

        for window in windows:

            try:

                title = (
                    window.title
                    .strip()
                    .lower()
                )

            except Exception:

                continue

            if not title:
                continue

            for keyword in keywords:

                if keyword in title:

                    matched_window = window
                    break

            if matched_window is not None:
                break

        # -----------------------------------------------------
        # NOT FOUND
        # -----------------------------------------------------

        if matched_window is None:

            self.speak(
                f"{app_name} is not currently open."
            )

            return

        # -----------------------------------------------------
        # ACTIVATE + CLOSE
        # -----------------------------------------------------

        try:

            print(
                "[MAX] Found window: "
                f"{matched_window.title}"
            )

            try:

                if matched_window.isMinimized:
                    matched_window.restore()

            except Exception:
                pass

            matched_window.activate()

            time.sleep(0.5)

            pyautogui.hotkey(
                "alt",
                "f4",
            )

            self.speak(
                f"Closed {app_name}."
            )

        except Exception as exc:

            print(
                f"[MAX] Named close error: {exc}"
            )

            self.speak(
                f"I could not close {app_name}."
            )

    # =========================================================
    # CLOSE COMMAND HANDLER
    # =========================================================

    def handle_close_command(
        self,
        command: str,
    ) -> bool:

        # -----------------------------------------------------
        # GENERIC ACTIVE-WINDOW COMMANDS
        # -----------------------------------------------------

        generic_commands = {
            "close",
            "close window",
            "close this window",
            "close current window",
            "close active window",
            "close application",
            "close the application",
            "close this application",
            "close current application",
        }

        if command in generic_commands:

            self.close_active_window()

            return True

        # -----------------------------------------------------
        # NAMED CLOSE
        #
        # close notepad
        # close chrome
        # close calculator
        # close browser
        # close web
        # close web search
        # -----------------------------------------------------

        match = re.match(
            r"^(?:close|exit)\s+(.+)$",
            command,
            flags=re.IGNORECASE,
        )

        if not match:
            return False

        target = (
            match.group(1)
            .strip()
        )

        # -----------------------------------------------------
        # MAX itself
        # -----------------------------------------------------

        if target in {
            "max",
            "assistant",
            "the assistant",
            "the max",
        }:

            self.shutdown()

            return True

        # -----------------------------------------------------
        # BROWSER ALIASES
        # -----------------------------------------------------

        if target in {
            "browser",
            "web",
            "web search",
        }:

            self.close_named_application(
                "browser"
            )

            return True

        # -----------------------------------------------------
        # FIND REGISTERED APPLICATION
        # -----------------------------------------------------

        app_name = (
            self.find_application_in_command(
                target
            )
        )

        if app_name:

            self.close_named_application(
                app_name
            )

            return True

        # -----------------------------------------------------
        # UNKNOWN TARGET
        # -----------------------------------------------------

        self.speak(
            f"I don't know which application "
            f"{target} refers to."
        )

        return True

    # =========================================================
    # DICTATION STATUS
    # =========================================================

    def _dictation_status(
        self,
        message,
    ):

        print(
            f"[MAX DICTATION] {message}"
        )

    # =========================================================
    # DICTATION FINISHED
    # =========================================================

    def _dictation_finished(self):

        self.dictation_active = False
        self.dictation_engine = None

        print(
            "[MAX] Dictation finished. "
            "Normal MAX mode restored."
        )

        # Confirm that voice typing has stopped.
        self.speak("Typing mode stopped.")

    # =========================================================
    # START DICTATION
    # =========================================================

    def start_dictation(self):

        if self.dictation_active:

            self.speak(
                "Typing mode is already active."
            )

            return

        print(
            "[MAX] Starting Whisper typing mode."
        )

        try:

            self.dictation_engine = (
                DictationEngine(
                    model_name="base",
                    max_segment_seconds=8.0,
                    silence_seconds=0.9,
                    minimum_speech_seconds=0.35,
                    threshold_multiplier=2.2,
                    minimum_threshold=0.008,
                    typing_interval=0.01,
                    on_status=self._dictation_status,
                    on_stop=self._dictation_finished,
                )
            )

            self.dictation_active = True

            started = (
                self.dictation_engine.start()
            )

            if not started:

                self.dictation_active = False
                self.dictation_engine = None

                self.speak(
                    "I could not start typing mode."
                )

                return

            self.speak(
                "Typing mode started."
            )

        except Exception as exc:

            self.dictation_active = False
            self.dictation_engine = None

            print(
                f"[MAX] Dictation start error: {exc}"
            )

            self.speak(
                "I could not start typing mode."
            )

    # =========================================================
    # STOP DICTATION
    # =========================================================

    def stop_dictation(
        self,
        speak_response=True,
    ):

        if not self.dictation_active:

            if speak_response:

                self.speak(
                    "Typing mode is not active."
                )

            return

        print(
            "[MAX] Stopping typing mode."
        )

        if self.dictation_engine is not None:

            self.dictation_engine.stop()

        self.dictation_active = False

        if speak_response:

            self.speak(
                "Typing mode stopped."
            )

    # =========================================================
    # PAUSE DICTATION
    # =========================================================

    def pause_dictation(self):

        if not self.dictation_active:

            self.speak(
                "Typing mode is not active."
            )

            return

        if self.dictation_engine is not None:

            self.dictation_engine.pause()

        self.speak(
            "Typing paused."
        )

    # =========================================================
    # RESUME DICTATION
    # =========================================================

    def resume_dictation(self):

        if not self.dictation_active:

            self.speak(
                "Typing mode is not active."
            )

            return

        if self.dictation_engine is not None:

            self.dictation_engine.resume()

        self.speak(
            "Typing resumed."
        )

    # =========================================================
    # LIST APPLICATIONS
    # =========================================================

    def list_applications(self):

        applications = (
            self.app_controller
            .get_supported_applications()
        )

        unique = sorted(
            set(applications)
        )

        print()
        print(
            "[MAX] Supported applications:"
        )

        for application in unique:

            print(
                f" - {application}"
            )

        print()

        self.speak(
            "I can open more than twenty "
            "applications."
        )

    # =========================================================
    # DATE
    # =========================================================

    def tell_date(self):

        today = datetime.datetime.now()

        formatted = today.strftime(
            "%A, %d %B %Y"
        )

        self.speak(
            f"Today's date is {formatted}."
        )

    # =========================================================
    # TIME
    # =========================================================

    def tell_time(self):

        now = datetime.datetime.now()

        formatted = now.strftime(
            "%I:%M %p"
        )

        self.speak(
            f"The time is {formatted}."
        )

    # =========================================================
    # WEB SEARCH
    # =========================================================

    def web_search(
        self,
        query: str,
    ):

        query = query.strip()

        if not query:

            self.speak(
                "Please tell me what to search."
            )

            return

        self.speak(
            f"Searching the web for {query}."
        )

        url = (
            "https://www.google.com/search?q="
            + query.replace(
                " ",
                "+",
            )
        )

        webbrowser.open(url)

    # =========================================================
    # LOCATION
    # =========================================================

    def search_location(
        self,
        location: str,
    ):

        location = location.strip()

        if not location:

            self.speak(
                "Please tell me the location."
            )

            return

        self.speak(
            f"Opening maps for {location}."
        )

        url = (
            "https://www.google.com/maps/search/"
            + location.replace(
                " ",
                "+",
            )
        )

        webbrowser.open(url)

    # =========================================================
    # COPY
    # =========================================================

    def copy(self):

        try:

            pyautogui.hotkey(
                "ctrl",
                "c",
            )

            self.speak(
                "Copied."
            )

        except Exception as exc:

            print(
                f"[MAX] Copy error: {exc}"
            )

            self.speak(
                "I could not copy the selection."
            )

    # =========================================================
    # PASTE
    # =========================================================

    def paste(self):

        try:

            pyautogui.hotkey(
                "ctrl",
                "v",
            )

            self.speak(
                "Pasted."
            )

        except Exception as exc:

            print(
                f"[MAX] Paste error: {exc}"
            )

            self.speak(
                "I could not paste."
            )

    # =========================================================
    # LIST FILES
    # =========================================================

    def list_files(self):

        try:

            current = os.getcwd()

            entries = os.listdir(
                current
            )

            entries = sorted(
                entries,
                key=lambda item: item.lower(),
            )

            print()
            print(
                f"[MAX] Files in: {current}"
            )

            if not entries:

                self.speak(
                    "The folder is empty."
                )

                return

            for index, item in enumerate(
                entries,
                start=1,
            ):

                print(
                    f"{index}. {item}"
                )

            self.speak(
                f"There are {len(entries)} "
                f"items in this folder."
            )

        except Exception as exc:

            print(
                f"[MAX] File listing error: {exc}"
            )

            self.speak(
                "I could not list the files."
            )

    # =========================================================
    # GO BACK
    # =========================================================

    def go_back(self):

        try:

            current = os.getcwd()

            parent = os.path.dirname(
                current
            )

            if parent == current:

                self.speak(
                    "You are already at "
                    "the top level."
                )

                return

            os.chdir(parent)

            print(
                f"[MAX] Current folder: "
                f"{os.getcwd()}"
            )

            self.speak(
                "Moved to the previous folder."
            )

        except Exception as exc:

            print(
                f"[MAX] Back error: {exc}"
            )

            self.speak(
                "I could not go back."
            )

    # =========================================================
    # OPEN FILE BY NUMBER
    # =========================================================

    def open_file_by_number(
        self,
        number: int,
    ):

        try:

            entries = sorted(
                os.listdir(
                    os.getcwd()
                ),
                key=lambda item: item.lower(),
            )

            if (
                number < 1
                or number > len(entries)
            ):

                self.speak(
                    "That file number is invalid."
                )

                return

            selected = entries[
                number - 1
            ]

            path = os.path.abspath(
                selected
            )

            print(
                f"[MAX] Opening: {path}"
            )

            os.startfile(path)

            self.speak(
                f"Opening {selected}."
            )

        except Exception as exc:

            print(
                f"[MAX] Open file error: {exc}"
            )

            self.speak(
                "I could not open that item."
            )

    # =========================================================
    # GESTURE CONTROLLER
    # =========================================================

    def _create_gesture_controller(self):

        try:

            from modules.hand_gesture.hand_mouse import (
                HandGestureMouse,
            )

            return HandGestureMouse()

        except Exception as exc:

            print(
                "[MAX] HandGestureMouse import failed: "
                f"{exc}"
            )

            return None

    # =========================================================
    # START GESTURE
    # =========================================================

    def start_gesture_recognition(self):

        if (
            self.gesture_controller is not None
            and self.gesture_thread is not None
            and self.gesture_thread.is_alive()
        ):

            self.speak(
                "Gesture recognition is already running."
            )

            return

        controller = (
            self._create_gesture_controller()
        )

        if controller is None:

            self.speak(
                "I could not start gesture recognition."
            )

            return

        self.gesture_controller = controller

        def run_controller():

            try:

                controller.start()

            except Exception as exc:

                print(
                    "[MAX] Gesture thread error: "
                    f"{exc}"
                )

        self.gesture_thread = threading.Thread(
            target=run_controller,
            daemon=True,
        )

        self.gesture_thread.start()

        self.speak(
            "Gesture recognition started."
        )

    # =========================================================
    # STOP GESTURE
    # =========================================================

    def stop_gesture_recognition(self):

        if self.gesture_controller is None:

            self.speak(
                "Gesture recognition is already stopped."
            )

            return

        controller = (
            self.gesture_controller
        )

        try:

            if hasattr(
                controller,
                "stop",
            ):

                controller.stop()

            if (
                self.gesture_thread is not None
                and self.gesture_thread.is_alive()
            ):

                self.gesture_thread.join(
                    timeout=1.0
                )

        except Exception as exc:

            print(
                f"[MAX] Gesture stop error: {exc}"
            )

        finally:

            self.gesture_controller = None
            self.gesture_thread = None

        self.speak(
            "Gesture recognition stopped."
        )

    # =========================================================
    # SHUTDOWN
    # =========================================================

    def shutdown(self):

        if self.dictation_active:

            self.stop_dictation(
                speak_response=False
            )

        if self.gesture_controller is not None:

            self.stop_gesture_recognition()

        self.running = False

        self.speak(
            "Goodbye."
        )

    # =========================================================
    # COMMAND PROCESSOR
    # =========================================================

    def respond(
        self,
        raw_command: str,
    ):

        if not raw_command:
            return

        command = self.clean_command(
            raw_command
        )

        print(
            f"[MAX] Processed command: {command}"
        )

        if not command:
            return

        # =====================================================
        # SLEEP / WAKE
        # =====================================================

        if self.sleeping:

            if self.contains_any(
                command,
                [
                    "wake",
                    "wake up",
                    "resume",
                    "continue",
                ],
            ):

                self.sleeping = False

                self.speak(
                    "I am awake."
                )

            return

        if self.contains_any(
            command,
            [
                "go to sleep",
                "sleep",
                "sleep mode",
            ],
        ):

            self.sleeping = True

            self.speak(
                "Entering sleep mode."
            )

            return

        # =====================================================
        # EXIT MAX
        # =====================================================

        if self.contains_any(
            command,
            [
                "exit",
                "quit",
                "shutdown max",
                "close max",
                "goodbye",
                "bye",
            ],
        ):

            self.shutdown()

            return

        # =====================================================
        # GREETING
        # =====================================================

        if self.contains_any(
            command,
            [
                "hello",
                "hi",
                "hey",
                "good morning",
                "good afternoon",
                "good evening",
            ],
        ):

            self.speak(
                "Hello. I am MAX. "
                "How can I help you?"
            )

            return

        # =====================================================
        # NAME
        # =====================================================

        if (
            "your name" in command
            or "who are you" in command
        ):

            self.speak(
                "My name is MAX, "
                "your touchless computer assistant."
            )

            return

        # =====================================================
        # DATE
        # =====================================================

        if (
            "what is the date" in command
            or "what's the date" in command
            or "today's date" in command
            or "tell me the date" in command
        ):

            self.tell_date()

            return

        # =====================================================
        # TIME
        # =====================================================

        if (
            "what is the time" in command
            or "what's the time" in command
            or "current time" in command
            or "tell me the time" in command
        ):

            self.tell_time()

            return

        # =====================================================
        # START TYPING
        # =====================================================

        if (
            command == "start typing"
            or command == "start typing mode"
            or command == "begin typing"
            or command == "start dictation"
        ):

            self.start_dictation()

            return

        # =====================================================
        # STOP TYPING
        # =====================================================

        if (
            command == "stop typing"
            or command == "stop typing mode"
            or command == "stop dictation"
        ):

            self.stop_dictation()

            return

        # =====================================================
        # PAUSE TYPING
        # =====================================================

        if (
            command == "pause typing"
            or command == "pause typing mode"
            or command == "pause dictation"
        ):

            self.pause_dictation()

            return

        # =====================================================
        # RESUME TYPING
        # =====================================================

        if (
            command == "resume typing"
            or command == "resume typing mode"
            or command == "resume dictation"
            or command == "continue typing"
        ):

            self.resume_dictation()

            return

        # =====================================================
        # CLOSE WINDOW / APPLICATION
        # =====================================================

        if self.handle_close_command(
            command
        ):

            return

        # =====================================================
        # LIST APPLICATIONS
        # =====================================================

        if (
            "list applications" in command
            or "show applications" in command
            or "supported applications" in command
            or "what applications can you open" in command
        ):

            self.list_applications()

            return

        # =====================================================
        # GESTURE START / STOP
        # =====================================================

        gesture_words = [
            "gesture",
            "gesture recognition",
            "hand gesture",
        ]

        is_gesture_command = (
            self.contains_any(
                command,
                gesture_words,
            )
        )

        if is_gesture_command:

            # START
            if self.contains_any(
                command,
                [
                    "start",
                    "launch",
                    "enable",
                    "activate",
                    "turn on",
                ],
            ):

                print(
                    "[MAX] Gesture START "
                    "command detected."
                )

                self.start_gesture_recognition()

                return

            # STOP
            if self.contains_any(
                command,
                [
                    "stop",
                    "top",
                    "disable",
                    "deactivate",
                    "close",
                    "turn off",
                    "shut down",
                ],
            ):

                print(
                    "[MAX] Gesture STOP "
                    "command detected."
                )

                self.stop_gesture_recognition()

                return

        # =====================================================
        # COPY
        # =====================================================

        if command in {
            "copy",
            "copy this",
        }:

            self.copy()

            return

        # =====================================================
        # PASTE
        # =====================================================

        if command in {
            "paste",
            "paste this",
        }:

            self.paste()

            return

        # =====================================================
        # LIST FILES
        # =====================================================

        if (
            command == "list"
            or "list files" in command
            or "show files" in command
        ):

            self.list_files()

            return

        # =====================================================
        # GO BACK
        # =====================================================

        if (
            command == "back"
            or "go back" in command
            or "previous folder" in command
        ):

            self.go_back()

            return

        # =====================================================
        # OPEN FILE BY NUMBER
        # =====================================================

        file_match = re.search(
            r"(?:open|launch)\s+"
            r"(?:file|item)?\s*"
            r"(\d+)$",
            command,
            flags=re.IGNORECASE,
        )

        if file_match:

            number = int(
                file_match.group(1)
            )

            self.open_file_by_number(
                number
            )

            return

        # =====================================================
        # LOCATION
        # =====================================================

        location_match = re.search(
            r"(?:search|find|show|open)\s+"
            r"(?:location|place|maps?)\s+"
            r"(?:for|of)?\s*(.+)$",
            command,
            flags=re.IGNORECASE,
        )

        if location_match:

            location = (
                location_match
                .group(1)
                .strip()
            )

            self.search_location(
                location
            )

            return

        # =====================================================
        # WEB SEARCH
        # =====================================================

        search_match = re.search(
            r"(?:search|google|look up)"
            r"\s+(?:for\s+)?(.+)$",
            command,
            flags=re.IGNORECASE,
        )

        if search_match:

            query = (
                search_match
                .group(1)
                .strip()
            )

            self.web_search(
                query
            )

            return

        # =====================================================
        # APPLICATION COMMAND
        # =====================================================

        if self.handle_application_command(
            command
        ):

            return

        # =====================================================
        # UNKNOWN COMMAND
        # =====================================================

        self.speak(
            "I did not understand that command."
        )

    # =========================================================
    # MAIN LOOP
    # =========================================================

    def run(self):

        self.speak(
            "MAX is ready."
        )

        while self.running:

            try:

                # Dictation engine owns the microphone.
                if self.dictation_active:

                    time.sleep(
                        0.2
                    )

                    continue

                command = self.listen()

                if not command:
                    continue

                self.respond(
                    command
                )

            except KeyboardInterrupt:

                print(
                    "\n[MAX] Keyboard interrupt."
                )

                self.shutdown()

                break

            except Exception as exc:

                print(
                    f"[MAX] Main loop error: {exc}"
                )

                self.speak(
                    "An error occurred "
                    "while processing the command."
                )


# =============================================================
# RUN MAX
# =============================================================

def run_max():

    assistant = MAX()
    assistant.run()


if __name__ == "__main__":

    run_max()