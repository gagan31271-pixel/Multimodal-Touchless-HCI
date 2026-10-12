# ============================================================
# SPEECH ENGINE
# Windows SAPI Direct Voice Control
# ============================================================

import threading

import pythoncom
import win32com.client

from config import (
    TTS_RATE,
    TTS_VOLUME,
    TTS_VOICE_NAME,
    TTS_MAX_CHARACTERS,
)


class SpeechEngine:

    def __init__(self):

        # ----------------------------------------------------
        # Initialize COM for this thread
        # ----------------------------------------------------

        pythoncom.CoInitialize()

        # ----------------------------------------------------
        # Windows SAPI speech engine
        # ----------------------------------------------------

        self.engine = (
            win32com.client.Dispatch(
                "SAPI.SpVoice"
            )
        )

        # ----------------------------------------------------
        # Thread safety
        # ----------------------------------------------------

        self.lock = threading.Lock()

        # ----------------------------------------------------
        # Selected voice
        # ----------------------------------------------------

        self.selected_voice = None

        # ----------------------------------------------------
        # Speech settings
        #
        # SAPI rate:
        # -10 = very slow
        #  0  = normal
        # +10 = very fast
        # ----------------------------------------------------

        self.engine.Rate = (
            self.convert_rate(
                TTS_RATE
            )
        )

        # SAPI volume: 0-100

        self.engine.Volume = int(
            max(
                0.0,
                min(
                    1.0,
                    TTS_VOLUME
                )
            )
            * 100
        )

        # ----------------------------------------------------
        # Select requested voice
        # ----------------------------------------------------

        if TTS_VOICE_NAME:

            self.set_voice(
                TTS_VOICE_NAME
            )

        # ----------------------------------------------------
        # Display active voice
        # ----------------------------------------------------

        print(
            f"TTS active voice: "
            f"{self.get_active_voice_name()}"
        )

    # ========================================================
    # CONVERT PYTTSX3-STYLE RATE TO SAPI RATE
    # ========================================================

    @staticmethod
    def convert_rate(rate):

        # pyttsx3 commonly uses around 150-200
        # while SAPI uses approximately -10 to +10.
        #
        # 135 -> -2
        # 150 -> 0
        # 170 -> 2
        # 185 -> 4

        sapi_rate = round(
            (rate - 150) / 10
        )

        return max(
            -10,
            min(
                10,
                sapi_rate
            )
        )

    # ========================================================
    # GET AVAILABLE VOICES
    # ========================================================

    def get_voices(self):

        voices = []

        voice_collection = (
            self.engine.GetVoices()
        )

        for index in range(
            voice_collection.Count
        ):

            voice = voice_collection.Item(
                index
            )

            voices.append(
                voice
            )

        return voices

    # ========================================================
    # GET ACTIVE VOICE NAME
    # ========================================================

    def get_active_voice_name(self):

        try:

            voice = self.engine.Voice

            return voice.GetDescription()

        except Exception:

            return "Unknown"

    # ========================================================
    # SET VOICE
    # ========================================================

    def set_voice(
        self,
        voice_name
    ):

        if not voice_name:

            return False

        requested = (
            voice_name
            .strip()
            .lower()
        )

        voices = self.get_voices()

        selected = None

        # ----------------------------------------------------
        # Exact / partial voice-name matching
        # ----------------------------------------------------

        for voice in voices:

            try:

                description = (
                    voice.GetDescription()
                    or ""
                )

                description_lower = (
                    description
                    .lower()
                )

                if (
                    requested
                    ==
                    description_lower
                    or
                    requested
                    in
                    description_lower
                ):

                    selected = voice

                    break

            except Exception:

                continue

        # ----------------------------------------------------
        # Try voice token ID
        # ----------------------------------------------------

        if selected is None:

            for voice in voices:

                try:

                    voice_id = (
                        voice.Id
                        or ""
                    )

                    if (
                        requested
                        in
                        voice_id.lower()
                    ):

                        selected = voice

                        break

                except Exception:

                    continue

        # ----------------------------------------------------
        # Voice not found
        # ----------------------------------------------------

        if selected is None:

            print(
                f"TTS voice not found: "
                f"{voice_name}"
            )

            return False

        # ----------------------------------------------------
        # Set SAPI voice directly
        # ----------------------------------------------------

        try:

            self.engine.Voice = selected

            self.selected_voice = (
                selected.GetDescription()
            )

            active_name = (
                self.get_active_voice_name()
            )

            print(
                f"Selected TTS voice: "
                f"{self.selected_voice}"
            )

            print(
                f"Verified TTS voice: "
                f"{active_name}"
            )

            return (
                active_name
                ==
                self.selected_voice
            )

        except Exception as error:

            print(
                f"Voice selection error: "
                f"{error}"
            )

            return False

    # ========================================================
    # SPEAK
    # ========================================================

    def speak(
        self,
        text
    ):

        if not text:

            return

        text = str(
            text
        ).strip()

        if not text:

            return

        # ----------------------------------------------------
        # Limit OCR text
        # ----------------------------------------------------

        if (
            len(text)
            >
            TTS_MAX_CHARACTERS
        ):

            text = (
                text[:TTS_MAX_CHARACTERS]
                +
                ". The remaining text was not spoken."
            )

        # ----------------------------------------------------
        # Speak using SAPI
        # ----------------------------------------------------

        with self.lock:

            try:

                # Re-apply selected voice.

                if self.selected_voice:

                    self.set_voice(
                        self.selected_voice
                    )

                # Synchronous speech.
                #
                # Flags = 0 means wait until
                # speech finishes.

                self.engine.Speak(
                    text,
                    0
                )

            except Exception as error:

                print(
                    f"TTS speech error: "
                    f"{error}"
                )

    # ========================================================
    # STOP
    # ========================================================

    def stop(self):

        with self.lock:

            try:

                # 2 = purge pending speech

                self.engine.Speak(
                    "",
                    2
                )

            except Exception:

                pass

    # ========================================================
    # VOICE INFORMATION
    # ========================================================

    def get_voice_info(self):

        result = []

        for voice in self.get_voices():

            try:

                result.append(
                    {
                        "name": (
                            voice.GetDescription()
                        ),
                        "id": voice.Id,
                    }
                )

            except Exception:

                pass

        return result

    # ========================================================
    # CLOSE
    # ========================================================

    def close(self):

        try:

            self.stop()

        finally:

            pythoncom.CoUninitialize()