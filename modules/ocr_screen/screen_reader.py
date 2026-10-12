# ============================================================
# SCREEN READER
# Full-Screen OCR + Selective Region OCR + TTS
# ============================================================

import time

import cv2
import numpy as np
import pyautogui

from config import (
    TESSERACT_PATH,
    OCR_LANGUAGE,
    OCR_MIN_CONFIDENCE,
    OCR_SCREENSHOT_DELAY,

    OCR_CROP_TOP,
    OCR_CROP_BOTTOM,
    OCR_CROP_LEFT,
    OCR_CROP_RIGHT,

    OCR_MIN_REGION_WIDTH,
    OCR_MIN_REGION_HEIGHT,
    OCR_SELECTION_WINDOW_TITLE,
    OCR_SELECTION_LINE_THICKNESS,
)

from modules.ocr_screen.ocr_engine import OCREngine
from modules.speech_engine import SpeechEngine


class ScreenReader:

    def __init__(self):

        # ----------------------------------------------------
        # OCR engine
        # ----------------------------------------------------

        self.ocr = OCREngine(
            tesseract_path=TESSERACT_PATH,
            language=OCR_LANGUAGE,
            min_confidence=OCR_MIN_CONFIDENCE,
        )

        # ----------------------------------------------------
        # Speech engine
        # ----------------------------------------------------

        self.speech = SpeechEngine()

        # ----------------------------------------------------
        # Last result
        # ----------------------------------------------------

        self.last_text = ""

        self.last_confidence = 0.0

        self.last_word_count = 0

    # ========================================================
    # CAPTURE SCREEN
    # ========================================================

    @staticmethod
    def capture_screen():

        time.sleep(
            OCR_SCREENSHOT_DELAY
        )

        return pyautogui.screenshot()

    # ========================================================
    # CROP CONFIGURED CONTENT REGION
    # ========================================================

    @staticmethod
    def crop_content_region(
        screenshot
    ):

        width, height = screenshot.size

        left = max(
            0,
            OCR_CROP_LEFT
        )

        top = max(
            0,
            OCR_CROP_TOP
        )

        right = min(
            width,
            width - OCR_CROP_RIGHT
        )

        bottom = min(
            height,
            height - OCR_CROP_BOTTOM
        )

        if right <= left:
            right = width

        if bottom <= top:
            bottom = height

        return screenshot.crop(
            (
                left,
                top,
                right,
                bottom,
            )
        )

    # ========================================================
    # OCR IMAGE
    # ========================================================

    def _process_image(
        self,
        image,
        speak=True
    ):

        result = self.ocr.get_info(
            image
        )

        self.last_text = result["text"]

        self.last_confidence = (
            result["average_confidence"]
        )

        self.last_word_count = (
            result["word_count"]
        )

        if (
            speak
            and
            self.last_text
        ):

            self.speech.speak(
                self.last_text
            )

        return {
            "text": self.last_text,

            "word_count": (
                self.last_word_count
            ),

            "average_confidence": (
                self.last_confidence
            ),
        }

    # ========================================================
    # FULL SCREEN OCR
    # ========================================================

    def read_screen(
        self,
        speak=True
    ):

        screenshot = (
            self.capture_screen()
        )

        content_region = (
            self.crop_content_region(
                screenshot
            )
        )

        return self._process_image(
            content_region,
            speak=speak
        )

    # ========================================================
    # GET FULL SCREEN IMAGE
    #
    # Used by the selection tool.
    # ========================================================

    @staticmethod
    def get_screen_image():

        screenshot = (
            pyautogui.screenshot()
        )

        return cv2.cvtColor(
            np.array(screenshot),
            cv2.COLOR_RGB2BGR
        )

    # ========================================================
    # SELECT OCR REGION
    #
    # User drags a rectangle over the screen.
    # Only that region is OCR'd.
    # ========================================================

    def select_region(self):

        screen = self.get_screen_image()

        original = screen.copy()

        selection = {
            "start_x": None,
            "start_y": None,
            "end_x": None,
            "end_y": None,
            "selecting": False,
            "finished": False,
        }

        window_name = (
            OCR_SELECTION_WINDOW_TITLE
        )

        # ----------------------------------------------------
        # Mouse callback
        # ----------------------------------------------------

        def mouse_callback(
            event,
            x,
            y,
            flags,
            param
        ):

            if event == cv2.EVENT_LBUTTONDOWN:

                selection["start_x"] = x
                selection["start_y"] = y

                selection["end_x"] = x
                selection["end_y"] = y

                selection["selecting"] = True

            elif (
                event
                ==
                cv2.EVENT_MOUSEMOVE
            ):

                if selection["selecting"]:

                    selection["end_x"] = x
                    selection["end_y"] = y

            elif (
                event
                ==
                cv2.EVENT_LBUTTONUP
            ):

                if selection["selecting"]:

                    selection["end_x"] = x
                    selection["end_y"] = y

                    selection["selecting"] = False
                    selection["finished"] = True

        # ----------------------------------------------------
        # Create selection window
        # ----------------------------------------------------

        cv2.namedWindow(
            window_name,
            cv2.WINDOW_NORMAL
        )

        cv2.setWindowProperty(
            window_name,
            cv2.WND_PROP_FULLSCREEN,
            cv2.WINDOW_FULLSCREEN
        )

        cv2.setMouseCallback(
            window_name,
            mouse_callback
        )

        while True:

            display = original.copy()

            # ------------------------------------------------
            # Draw current selection
            # ------------------------------------------------

            if (
                selection["start_x"]
                is not None
            ):

                x1 = min(
                    selection["start_x"],
                    selection["end_x"]
                )

                y1 = min(
                    selection["start_y"],
                    selection["end_y"]
                )

                x2 = max(
                    selection["start_x"],
                    selection["end_x"]
                )

                y2 = max(
                    selection["start_y"],
                    selection["end_y"]
                )

                cv2.rectangle(
                    display,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    OCR_SELECTION_LINE_THICKNESS
                )

            # ------------------------------------------------
            # Instructions
            # ------------------------------------------------

            cv2.rectangle(
                display,
                (20, 20),
                (530, 80),
                (0, 0, 0),
                -1
            )

            cv2.putText(
                display,
                "Drag to select text | ENTER = OCR | ESC = Cancel",
                (35, 58),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2
            )

            cv2.imshow(
                window_name,
                display
            )

            key = (
                cv2.waitKey(20)
                &
                0xFF
            )

            # ------------------------------------------------
            # ENTER -> process selection
            # ------------------------------------------------

            if key in (
                13,
                10
            ):

                if selection["finished"]:

                    break

            # ------------------------------------------------
            # ESC -> cancel
            # ------------------------------------------------

            if key == 27:

                cv2.destroyWindow(
                    window_name
                )

                return {
                    "cancelled": True,
                    "text": "",
                    "word_count": 0,
                    "average_confidence": 0.0,
                }

        cv2.destroyWindow(
            window_name
        )

        # ----------------------------------------------------
        # Validate selection
        # ----------------------------------------------------

        x1 = min(
            selection["start_x"],
            selection["end_x"]
        )

        y1 = min(
            selection["start_y"],
            selection["end_y"]
        )

        x2 = max(
            selection["start_x"],
            selection["end_x"]
        )

        y2 = max(
            selection["start_y"],
            selection["end_y"]
        )

        width = x2 - x1

        height = y2 - y1

        if (
            width < OCR_MIN_REGION_WIDTH
            or
            height < OCR_MIN_REGION_HEIGHT
        ):

            return {
                "cancelled": True,
                "text": "",
                "word_count": 0,
                "average_confidence": 0.0,
            }

        # ----------------------------------------------------
        # Crop selected region
        # ----------------------------------------------------

        selected_image = original[
            y1:y2,
            x1:x2
        ]

        # ----------------------------------------------------
        # OCR
        # ----------------------------------------------------

        result = self._process_image(
            selected_image,
            speak=True
        )

        result["cancelled"] = False

        result["region"] = (
            x1,
            y1,
            x2,
            y2
        )

        return result

    # ========================================================
    # SELECTIVE OCR WITHOUT AUTOMATIC SPEECH
    # ========================================================

    def select_and_extract_text(
        self
    ):

        screen = self.get_screen_image()

        original = screen.copy()

        selection = {
            "start_x": None,
            "start_y": None,
            "end_x": None,
            "end_y": None,
            "selecting": False,
            "finished": False,
        }

        window_name = (
            OCR_SELECTION_WINDOW_TITLE
        )

        def mouse_callback(
            event,
            x,
            y,
            flags,
            param
        ):

            if event == cv2.EVENT_LBUTTONDOWN:

                selection["start_x"] = x
                selection["start_y"] = y

                selection["end_x"] = x
                selection["end_y"] = y

                selection["selecting"] = True

            elif (
                event
                ==
                cv2.EVENT_MOUSEMOVE
            ):

                if selection["selecting"]:

                    selection["end_x"] = x
                    selection["end_y"] = y

            elif (
                event
                ==
                cv2.EVENT_LBUTTONUP
            ):

                selection["end_x"] = x
                selection["end_y"] = y

                selection["selecting"] = False
                selection["finished"] = True

        cv2.namedWindow(
            window_name,
            cv2.WINDOW_NORMAL
        )

        cv2.setWindowProperty(
            window_name,
            cv2.WND_PROP_FULLSCREEN,
            cv2.WINDOW_FULLSCREEN
        )

        cv2.setMouseCallback(
            window_name,
            mouse_callback
        )

        while True:

            display = original.copy()

            if (
                selection["start_x"]
                is not None
            ):

                x1 = min(
                    selection["start_x"],
                    selection["end_x"]
                )

                y1 = min(
                    selection["start_y"],
                    selection["end_y"]
                )

                x2 = max(
                    selection["start_x"],
                    selection["end_x"]
                )

                y2 = max(
                    selection["start_y"],
                    selection["end_y"]
                )

                cv2.rectangle(
                    display,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    OCR_SELECTION_LINE_THICKNESS
                )

            cv2.putText(
                display,
                "Drag to select | ENTER = Read | ESC = Cancel",
                (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

            cv2.imshow(
                window_name,
                display
            )

            key = (
                cv2.waitKey(20)
                &
                0xFF
            )

            if key in (
                13,
                10
            ):

                if selection["finished"]:

                    break

            if key == 27:

                cv2.destroyWindow(
                    window_name
                )

                return {
                    "cancelled": True,
                    "text": "",
                    "word_count": 0,
                    "average_confidence": 0.0,
                }

        cv2.destroyWindow(
            window_name
        )

        x1 = min(
            selection["start_x"],
            selection["end_x"]
        )

        y1 = min(
            selection["start_y"],
            selection["end_y"]
        )

        x2 = max(
            selection["start_x"],
            selection["end_x"]
        )

        y2 = max(
            selection["start_y"],
            selection["end_y"]
        )

        width = x2 - x1

        height = y2 - y1

        if (
            width < OCR_MIN_REGION_WIDTH
            or
            height < OCR_MIN_REGION_HEIGHT
        ):

            return {
                "cancelled": True,
                "text": "",
                "word_count": 0,
                "average_confidence": 0.0,
            }

        selected_image = original[
            y1:y2,
            x1:x2
        ]

        return self._process_image(
            selected_image,
            speak=False
        )

    # ========================================================
    # SPEAK TEXT
    # ========================================================

    def speak_text(
        self,
        text
    ):

        self.speech.speak(
            text
        )

    # ========================================================
    # STOP SPEECH
    # ========================================================

    def stop_speech(self):

        self.speech.stop()

    # ========================================================
    # STATUS
    # ========================================================

    def get_status(self):

        return {
            "text": self.last_text,
            "word_count": (
                self.last_word_count
            ),
            "average_confidence": (
                self.last_confidence
            ),
        }

    # ========================================================
    # CLOSE
    # ========================================================

    def close(self):

        self.speech.close()