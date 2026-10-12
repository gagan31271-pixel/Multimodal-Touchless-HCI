# ============================================================
# OCR ENGINE
# Screenshot -> Tesseract -> Clean Text
# ============================================================

import os
import shutil

import pytesseract

from PIL import Image


class OCREngine:

    def __init__(
        self,
        tesseract_path=None,
        language="eng",
        min_confidence=35,
    ):

        self.language = language

        self.min_confidence = (
            min_confidence
        )

        # ----------------------------------------------------
        # Find Tesseract executable
        # ----------------------------------------------------

        self.tesseract_path = (
            self.find_tesseract(
                tesseract_path
            )
        )

        if self.tesseract_path is None:

            raise FileNotFoundError(
                "Tesseract OCR executable was not found."
            )

        pytesseract.pytesseract.tesseract_cmd = (
            self.tesseract_path
        )

    # ========================================================
    # FIND TESSERACT
    # ========================================================

    @staticmethod
    def find_tesseract(
        configured_path=None
    ):

        candidates = []

        # ----------------------------------------------------
        # Configured path
        # ----------------------------------------------------

        if configured_path:

            candidates.append(
                configured_path
            )

        # ----------------------------------------------------
        # Standard Windows locations
        # ----------------------------------------------------

        candidates.extend(
            [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            ]
        )

        # ----------------------------------------------------
        # PATH
        # ----------------------------------------------------

        path_result = shutil.which(
            "tesseract"
        )

        if path_result:

            candidates.append(
                path_result
            )

        # ----------------------------------------------------
        # Validate candidates
        # ----------------------------------------------------

        for path in candidates:

            if (
                path
                and
                os.path.isfile(path)
            ):

                return path

        return None

    # ========================================================
    # OCR IMAGE
    # ========================================================

    def extract_text(
        self,
        image
    ):

        if image is None:

            return ""

        # ----------------------------------------------------
        # Run OCR
        # ----------------------------------------------------

        text = pytesseract.image_to_string(
            image,
            lang=self.language,
            config="--psm 6",
        )

        return self.clean_text(
            text
        )

    # ========================================================
    # OCR WITH CONFIDENCE FILTERING
    # ========================================================

    def extract_text_with_confidence(
        self,
        image
    ):

        if image is None:

            return {
                "text": "",
                "words": [],
            }

        data = pytesseract.image_to_data(
            image,
            lang=self.language,
            config="--psm 6",
            output_type=pytesseract.Output.DICT,
        )

        words = []

        for i in range(
            len(data["text"])
        ):

            raw_text = (
                data["text"][i]
                .strip()
            )

            if not raw_text:

                continue

            try:

                confidence = float(
                    data["conf"][i]
                )

            except (
                ValueError,
                TypeError
            ):

                confidence = 0.0

            if (
                confidence
                <
                self.min_confidence
            ):

                continue

            words.append(
                {
                    "text": raw_text,
                    "confidence": confidence,
                    "left": data["left"][i],
                    "top": data["top"][i],
                    "width": data["width"][i],
                    "height": data["height"][i],
                }
            )

        # ----------------------------------------------------
        # Reconstruct text
        # ----------------------------------------------------

        text = " ".join(
            word["text"]
            for word in words
        )

        return {
            "text": self.clean_text(
                text
            ),
            "words": words,
        }

    # ========================================================
    # CLEAN TEXT
    # ========================================================

    @staticmethod
    def clean_text(text):

        if not text:

            return ""

        lines = []

        for line in text.splitlines():

            line = line.strip()

            if not line:

                continue

            # Remove repeated spaces.

            line = " ".join(
                line.split()
            )

            lines.append(line)

        return "\n".join(
            lines
        )

    # ========================================================
    # GET OCR DETAILS
    # ========================================================

    def get_info(
        self,
        image
    ):

        result = (
            self.extract_text_with_confidence(
                image
            )
        )

        words = result["words"]

        if words:

            average_confidence = (
                sum(
                    word["confidence"]
                    for word in words
                )
                /
                len(words)
            )

        else:

            average_confidence = 0.0

        return {
            "text": result["text"],
            "word_count": len(words),
            "average_confidence": (
                average_confidence
            ),
            "words": words,
        }