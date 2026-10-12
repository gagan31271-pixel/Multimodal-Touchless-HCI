import os
import shutil
import subprocess
import time
import webbrowser
from typing import Optional

import pyautogui


class ApplicationController:
    """
    Windows application launcher and basic application interaction
    for the MAX voice assistant.
    """

    def __init__(self, launch_delay: float = 1.2):
        self.launch_delay = launch_delay

        # Application aliases -> Windows launch target
        self.applications = {
            # Windows built-in applications
            "calculator": "calc",
            "calc": "calc",

            "notepad": "notepad",

            "paint": "mspaint",
            "ms paint": "mspaint",

            "file explorer": "explorer",
            "explorer": "explorer",

            "command prompt": "cmd",
            "cmd": "cmd",

            "powershell": "powershell",

            "task manager": "taskmgr",
            "task manager": "taskmgr",

            "control panel": "control",

            "settings": "ms-settings:",

            "camera": "microsoft.windows.camera:",

            "snipping tool": "snippingtool",

            "terminal": "wt",
            "windows terminal": "wt",

            # Browsers
            "chrome": "chrome",
            "google chrome": "chrome",

            "edge": "msedge",
            "microsoft edge": "msedge",

            # Development
            "vscode": "code",
            "vs code": "code",
            "visual studio code": "code",

            # Microsoft Office
            "word": "winword",
            "microsoft word": "winword",

            "excel": "excel",
            "microsoft excel": "excel",

            "powerpoint": "powerpnt",
            "power point": "powerpnt",
            "ppt": "powerpnt",

            "outlook": "outlook",
            "microsoft outlook": "outlook",

            # Common desktop applications
            "spotify": "spotify",
            "discord": "discord",
            "whatsapp": "whatsapp",
            "steam": "steam",
        }

        self.browser_names = {
            "chrome",
            "google chrome",
            "edge",
            "microsoft edge",
        }

    # ---------------------------------------------------------
    # Normalization
    # ---------------------------------------------------------

    @staticmethod
    def normalize_name(name: str) -> str:
        name = name.lower().strip()

        # Remove unnecessary command words
        prefixes = [
            "the ",
            "application ",
            "app ",
        ]

        for prefix in prefixes:
            if name.startswith(prefix):
                name = name[len(prefix):]

        return name.strip()

    # ---------------------------------------------------------
    # Lookup
    # ---------------------------------------------------------

    def get_target(self, app_name: str) -> Optional[str]:
        app_name = self.normalize_name(app_name)
        return self.applications.get(app_name)

    # ---------------------------------------------------------
    # Launch
    # ---------------------------------------------------------

    def open_application(self, app_name: str) -> bool:
        """
        Launch an application by its friendly voice name.
        """

        app_name = self.normalize_name(app_name)
        target = self.get_target(app_name)

        if not target:
            print(f"[MAX APP] Unknown application: {app_name}")
            return False

        print(f"[MAX APP] Opening: {app_name}")
        print(f"[MAX APP] Target: {target}")

        try:
            # URI / Windows system protocol
            if target.endswith(":"):
                os.startfile(target)

            # Windows executables / commands
            else:
                self._launch_windows_target(target)

            time.sleep(self.launch_delay)

            print(f"[MAX APP] Successfully launched: {app_name}")
            return True

        except Exception as exc:
            print(f"[MAX APP] Launch failed: {exc}")
            return False

    # ---------------------------------------------------------
    # Windows launcher
    # ---------------------------------------------------------

    @staticmethod
    def _launch_windows_target(target: str):
        """
        Uses Windows START so that commands such as
        calc, chrome, winword, msedge, etc. can be resolved
        through Windows app registrations / PATH.
        """

        # First try PATH
        executable = shutil.which(target)

        if executable:
            subprocess.Popen(
                [executable],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return

        # Windows START command
        command = f'start "" "{target}"'

        subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    # ---------------------------------------------------------
    # Type text
    # ---------------------------------------------------------

    @staticmethod
    def type_text(text: str, interval: float = 0.015) -> bool:
        """
        Types text into the currently focused application.
        """

        if not text:
            return False

        print(f"[MAX APP] Typing: {text}")

        try:
            pyautogui.write(
                text,
                interval=interval,
            )
            return True

        except Exception as exc:
            print(f"[MAX APP] Typing failed: {exc}")
            return False

    # ---------------------------------------------------------
    # Browser detection
    # ---------------------------------------------------------

    def is_browser(self, app_name: str) -> bool:
        return self.normalize_name(app_name) in self.browser_names

    # ---------------------------------------------------------
    # Browser search
    # ---------------------------------------------------------

    def search_in_browser(
        self,
        app_name: str,
        query: str,
    ) -> bool:

        if not query:
            return False

        if not self.is_browser(app_name):
            return False

        print(f"[MAX APP] Searching in {app_name}: {query}")

        try:
            # Focus address bar
            pyautogui.hotkey("ctrl", "l")
            time.sleep(0.2)

            pyautogui.write(
                query,
                interval=0.015,
            )

            pyautogui.press("enter")

            return True

        except Exception as exc:
            print(f"[MAX APP] Browser search failed: {exc}")
            return False

    # ---------------------------------------------------------
    # Open application and type
    # ---------------------------------------------------------

    def open_and_type(
        self,
        app_name: str,
        text: str,
    ) -> bool:

        opened = self.open_application(app_name)

        if not opened:
            return False

        # Give application additional time to become active
        time.sleep(0.8)

        try:
            # Browsers should receive text through address bar.
            if self.is_browser(app_name):
                pyautogui.hotkey("ctrl", "l")
                time.sleep(0.2)

            return self.type_text(text)

        except Exception as exc:
            print(f"[MAX APP] Open and type failed: {exc}")
            return False

    # ---------------------------------------------------------
    # Open browser and search
    # ---------------------------------------------------------

    def open_and_search(
        self,
        app_name: str,
        query: str,
    ) -> bool:

        opened = self.open_application(app_name)

        if not opened:
            return False

        time.sleep(0.8)

        return self.search_in_browser(
            app_name,
            query,
        )

    # ---------------------------------------------------------
    # List supported applications
    # ---------------------------------------------------------

    def get_supported_applications(self):
        return sorted(
            set(self.applications.keys())
        )


if __name__ == "__main__":
    controller = ApplicationController()

    print("\nSupported applications:\n")

    for app in controller.get_supported_applications():
        print(" -", app)

    print("\nApplication controller ready.")