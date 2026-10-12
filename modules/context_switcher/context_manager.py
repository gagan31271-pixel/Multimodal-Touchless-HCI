"""
Automatic Application Context Manager

Detects the active Windows application and automatically loads
the corresponding context profile from:

    config/context_profiles.yaml

The manager checks the active window every 2 seconds.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import pygetwindow as gw
import yaml


class ContextManager:
    """Manages automatic application-based context switching."""

    def __init__(
        self,
        profile_file: Optional[str] = None,
        check_interval: float = 2.0,
        on_context_change: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        self.check_interval = check_interval
        self.on_context_change = on_context_change

        # ---------------------------------------------------------
        # Resolve project root reliably
        # context_manager.py is:
        # project/modules/context_switcher/context_manager.py
        #
        # parents[0] -> context_switcher
        # parents[1] -> modules
        # parents[2] -> project root
        # ---------------------------------------------------------
        self.project_root = Path(__file__).resolve().parents[2]

        if profile_file:
            self.profile_file = Path(profile_file)

            # Convert relative path to project-root-relative path
            if not self.profile_file.is_absolute():
                self.profile_file = self.project_root / self.profile_file
        else:
            self.profile_file = (
                self.project_root
                / "config"
                / "context_profiles.yaml"
            )

        # Runtime state
        self.profiles: Dict[str, Dict[str, Any]] = {}

        self.current_app: Optional[str] = None
        self.current_profile_name: str = "default"
        self.current_profile: Dict[str, Any] = {}

        self._running = False
        self._thread: Optional[threading.Thread] = None

        # Load profiles immediately
        self.load_profiles()

    # =========================================================
    # PROFILE LOADING
    # =========================================================

    def load_profiles(self) -> bool:
        """Load context profiles from YAML."""

        if not self.profile_file.exists():
            print(
                f"[CONTEXT] Profile file not found:\n"
                f"           {self.profile_file}"
            )

            self.profiles = {
                "default": {
                    "description": "Default desktop profile",
                    "window_keywords": [],
                    "gesture_mapping": {},
                }
            }

            return False

        try:
            with self.profile_file.open(
                "r",
                encoding="utf-8",
            ) as file:
                data = yaml.safe_load(file)

            if not isinstance(data, dict):
                raise ValueError(
                    "YAML root must contain a dictionary of profiles."
                )

            self.profiles = data.get("profiles", data)

            if not isinstance(self.profiles, dict):
                raise ValueError(
                    "The 'profiles' section must be a dictionary."
                )

            # Make sure default profile always exists
            self.profiles.setdefault(
                "default",
                {
                    "description": "Default desktop profile",
                    "window_keywords": [],
                    "gesture_mapping": {},
                },
            )

            print(
                f"[CONTEXT] Loaded {len(self.profiles)} profiles."
            )
            print(
                f"[CONTEXT] Profile file: {self.profile_file}"
            )

            return True

        except Exception as exc:
            print(
                f"[CONTEXT] Failed to load profiles: {exc}"
            )

            self.profiles = {
                "default": {
                    "description": "Default desktop profile",
                    "window_keywords": [],
                    "gesture_mapping": {},
                }
            }

            return False

    # =========================================================
    # ACTIVE WINDOW
    # =========================================================

    def get_active_window_title(self) -> str:
        """Return the title of the currently active window."""

        try:
            window = gw.getActiveWindow()

            if window is None:
                return ""

            title = window.title

            if title is None:
                return ""

            return title.strip()

        except Exception as exc:
            print(
                f"[CONTEXT] Unable to read active window: {exc}"
            )
            return ""

    # =========================================================
    # PROFILE MATCHING
    # =========================================================

    def find_profile(self, window_title: str) -> str:
        """
        Match active window title against profile keywords.

        Returns the profile name.
        """

        if not window_title:
            return "default"

        title_lower = window_title.lower()

        # Check all profiles except default first
        for profile_name, profile in self.profiles.items():

            if profile_name.lower() == "default":
                continue

            keywords = profile.get(
                "window_keywords",
                profile.get("keywords", []),
            )

            if not isinstance(keywords, list):
                continue

            for keyword in keywords:
                if not keyword:
                    continue

                if str(keyword).lower() in title_lower:
                    return profile_name

        return "default"

    # =========================================================
    # CONTEXT UPDATE
    # =========================================================

    def update_context(self) -> bool:
        """
        Detect active application and update the current context.

        Returns True when the context changes.
        """

        window_title = self.get_active_window_title()

        if not window_title:
            return False

        profile_name = self.find_profile(window_title)

        changed = (
            window_title != self.current_app
            or profile_name != self.current_profile_name
        )

        if not changed:
            return False

        self.current_app = window_title
        self.current_profile_name = profile_name

        self.current_profile = self.profiles.get(
            profile_name,
            self.profiles.get("default", {}),
        )

        print()
        print("[CONTEXT] Application changed")
        print(
            f"[CONTEXT] Active window : {self.current_app}"
        )
        print(
            f"[CONTEXT] Profile       : "
            f"{self.current_profile_name}"
        )
        print(
            f"[CONTEXT] Description   : "
            f"{self.current_profile.get('description', '')}"
        )

        if self.on_context_change:
            try:
                self.on_context_change(self.get_context())
            except Exception as exc:
                print(
                    f"[CONTEXT] Callback error: {exc}"
                )

        return True

    # =========================================================
    # BACKGROUND MONITOR
    # =========================================================

    def _monitor_loop(self) -> None:
        """Background monitoring loop."""

        while self._running:

            try:
                self.update_context()

            except Exception as exc:
                print(
                    f"[CONTEXT] Monitoring error: {exc}"
                )

            time.sleep(self.check_interval)

    # =========================================================
    # START
    # =========================================================

    def start(self) -> bool:
        """Start automatic context switching."""

        if self._running:
            print(
                "[CONTEXT] Context manager is already running."
            )
            return False

        # Detect initial context immediately
        self.update_context()

        self._running = True

        self._thread = threading.Thread(
            target=self._monitor_loop,
            name="ContextManagerThread",
            daemon=True,
        )

        self._thread.start()

        print(
            "[CONTEXT] Automatic context switching ACTIVE."
        )

        return True

    # =========================================================
    # STOP
    # =========================================================

    def stop(self) -> None:
        """Stop automatic context switching."""

        if not self._running:
            return

        self._running = False

        if (
            self._thread is not None
            and self._thread.is_alive()
            and threading.current_thread() != self._thread
        ):
            self._thread.join(timeout=3.0)

        self._thread = None

        print(
            "[CONTEXT] Automatic context switching STOPPED."
        )

    # =========================================================
    # STATE
    # =========================================================

    def is_running(self) -> bool:
        """Return whether context monitoring is active."""

        return self._running

    def get_context(self) -> Dict[str, Any]:
        """
        Return the current context information.
        """

        return {
            "application": self.current_app,
            "profile_name": self.current_profile_name,
            "description": self.current_profile.get(
                "description",
                "",
            ),
            "gesture_mapping": self.current_profile.get(
                "gesture_mapping",
                {},
            ),
            "profile": self.current_profile,
        }

    # =========================================================
    # GESTURE MAPPING
    # =========================================================

    def get_gesture_mapping(
        self,
        gesture: str,
    ) -> Optional[str]:
        """
        Return the action assigned to a gesture in the
        currently active application profile.
        """

        mapping = self.current_profile.get(
            "gesture_mapping",
            {},
        )

        if not isinstance(mapping, dict):
            return None

        return mapping.get(gesture)

    # =========================================================
    # PROFILE ACCESS
    # =========================================================

    def get_profile(
        self,
        profile_name: str,
    ) -> Optional[Dict[str, Any]]:
        """Return a specific profile."""

        return self.profiles.get(profile_name)

    def get_all_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Return all loaded profiles."""

        return self.profiles

    # =========================================================
    # CLEANUP
    # =========================================================

    def close(self) -> None:
        """Cleanly stop the context manager."""

        self.stop()

    # =========================================================
    # TEST
    # =========================================================


def context_change_callback(context: Dict[str, Any]) -> None:
    """Example callback used during standalone testing."""

    print(
        "[CALLBACK] Current profile:",
        context["profile_name"],
    )


def main() -> None:
    """Standalone ContextManager test."""

    print()
    print("=" * 60)
    print(" AUTOMATIC CONTEXT SWITCHER TEST")
    print("=" * 60)
    print()

    manager = ContextManager(
        check_interval=2.0,
        on_context_change=context_change_callback,
    )

    print(
        f"[CONTEXT] Project root : "
        f"{manager.project_root}"
    )

    print(
        f"[CONTEXT] YAML file    : "
        f"{manager.profile_file}"
    )

    print()

    if not manager.profiles:
        print(
            "[CONTEXT] No profiles loaded."
        )

    print(
        "[CONTEXT] Loaded profiles:"
    )

    for profile_name in manager.profiles:
        print(
            f"  - {profile_name}"
        )

    print()

    manager.start()

    print(
        "Press Ctrl+C to stop."
    )

    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print()
        print(
            "[CONTEXT] Stopping..."
        )

    finally:
        manager.stop()


if __name__ == "__main__":
    main()