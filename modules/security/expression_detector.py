# ============================================================
# FACIAL EXPRESSION DETECTOR
# ============================================================

import math

from config import (
    EXPRESSION_CALIBRATION_FRAMES,
    EXPRESSION_STABLE_FRAMES,
    EXPRESSION_EMA_ALPHA,

    SMILE_THRESHOLD,
    EYEBROW_THRESHOLD,
    MOUTH_OPEN_THRESHOLD,

    FROWN_THRESHOLD,

    SURPRISE_EYEBROW_THRESHOLD,
    SURPRISE_EYE_THRESHOLD,
    SURPRISE_MOUTH_THRESHOLD,
)


class ExpressionDetector:

    # ========================================================
    # MOUTH LANDMARKS
    # ========================================================

    MOUTH_LEFT = 61
    MOUTH_RIGHT = 291

    MOUTH_TOP = 13
    MOUTH_BOTTOM = 14

    # ========================================================
    # NOSE LANDMARKS
    # ========================================================

    NOSE_BOTTOM = 2

    # ========================================================
    # EYEBROW LANDMARKS
    # ========================================================

    LEFT_BROW_1 = 70
    LEFT_BROW_2 = 63

    RIGHT_BROW_1 = 300
    RIGHT_BROW_2 = 293

    # ========================================================
    # EYE LANDMARKS
    # ========================================================

    LEFT_EYE_TOP = 159
    LEFT_EYE_BOTTOM = 145

    RIGHT_EYE_TOP = 386
    RIGHT_EYE_BOTTOM = 374

    LEFT_EYE_LEFT = 33
    LEFT_EYE_RIGHT = 133

    RIGHT_EYE_LEFT = 362
    RIGHT_EYE_RIGHT = 263

    # ========================================================
    # FACE SIZE
    # ========================================================

    FACE_LEFT = 234
    FACE_RIGHT = 454

    FOREHEAD = 10
    CHIN = 152

    def __init__(self):

        # ----------------------------------------------------
        # Calibration
        # ----------------------------------------------------

        self.calibration_frames = 0

        self.neutral_smile = None
        self.neutral_eyebrow = None
        self.neutral_mouth = None
        self.neutral_eye = None
        self.neutral_frown = None

        # ----------------------------------------------------
        # Smoothed features
        # ----------------------------------------------------

        self.smoothed_smile = None
        self.smoothed_eyebrow = None
        self.smoothed_mouth = None
        self.smoothed_eye = None
        self.smoothed_frown = None

        # ----------------------------------------------------
        # Expression stability
        # ----------------------------------------------------

        self.previous_expression = "NEUTRAL"

        self.expression_frames = 0

        self.current_expression = "CALIBRATING"

    # ========================================================
    # DISTANCE
    # ========================================================

    @staticmethod
    def distance(a, b):

        return math.sqrt(
            (a.x - b.x) ** 2
            +
            (a.y - b.y) ** 2
            +
            (a.z - b.z) ** 2
        )

    # ========================================================
    # EMA SMOOTHING
    # ========================================================

    @staticmethod
    def smooth(
        previous,
        current,
        alpha
    ):

        if previous is None:

            return current

        return (
            alpha * current
            +
            (1 - alpha) * previous
        )

    # ========================================================
    # FACE WIDTH
    # ========================================================

    def get_face_width(self, landmarks):

        return self.distance(
            landmarks[self.FACE_LEFT],
            landmarks[self.FACE_RIGHT]
        )

    # ========================================================
    # FACE HEIGHT
    # ========================================================

    def get_face_height(self, landmarks):

        return self.distance(
            landmarks[self.FOREHEAD],
            landmarks[self.CHIN]
        )

    # ========================================================
    # SMILE FEATURE
    #
    # Positive value -> stronger smile tendency
    # ========================================================

    def get_smile_feature(self, landmarks):

        face_width = self.get_face_width(
            landmarks
        )

        if face_width <= 0:

            return 0.0

        left_corner = landmarks[
            self.MOUTH_LEFT
        ]

        right_corner = landmarks[
            self.MOUTH_RIGHT
        ]

        nose = landmarks[
            self.NOSE_BOTTOM
        ]

        mouth_width = self.distance(
            left_corner,
            right_corner
        )

        mouth_center_y = (
            left_corner.y
            +
            right_corner.y
        ) / 2.0

        vertical_lift = (
            nose.y
            -
            mouth_center_y
        ) / face_width

        normalized_width = (
            mouth_width
            /
            face_width
        )

        return (
            0.40 * normalized_width
            +
            0.60 * vertical_lift
        )

    # ========================================================
    # FROWN FEATURE
    #
    # Measures downward movement of the mouth corners
    # relative to the neutral mouth position.
    # ========================================================

    def get_frown_feature(self, landmarks):

        face_width = self.get_face_width(
            landmarks
        )

        if face_width <= 0:

            return 0.0

        left_corner = landmarks[
            self.MOUTH_LEFT
        ]

        right_corner = landmarks[
            self.MOUTH_RIGHT
        ]

        nose = landmarks[
            self.NOSE_BOTTOM
        ]

        mouth_center_y = (
            left_corner.y
            +
            right_corner.y
        ) / 2.0

        # Positive when corners move downward.

        downward_position = (
            mouth_center_y
            -
            nose.y
        ) / face_width

        return downward_position

    # ========================================================
    # EYEBROW FEATURE
    #
    # Larger value = eyebrows further above eyes.
    # ========================================================

    def get_eyebrow_feature(self, landmarks):

        face_height = self.get_face_height(
            landmarks
        )

        if face_height <= 0:

            return 0.0

        left_brow_y = (
            landmarks[
                self.LEFT_BROW_1
            ].y
            +
            landmarks[
                self.LEFT_BROW_2
            ].y
        ) / 2.0

        right_brow_y = (
            landmarks[
                self.RIGHT_BROW_1
            ].y
            +
            landmarks[
                self.RIGHT_BROW_2
            ].y
        ) / 2.0

        left_eye_y = (
            landmarks[
                self.LEFT_EYE_TOP
            ].y
            +
            landmarks[
                self.LEFT_EYE_BOTTOM
            ].y
        ) / 2.0

        right_eye_y = (
            landmarks[
                self.RIGHT_EYE_TOP
            ].y
            +
            landmarks[
                self.RIGHT_EYE_BOTTOM
            ].y
        ) / 2.0

        left_gap = (
            left_eye_y
            -
            left_brow_y
        )

        right_gap = (
            right_eye_y
            -
            right_brow_y
        )

        average_gap = (
            left_gap
            +
            right_gap
        ) / 2.0

        return (
            average_gap
            /
            face_height
        )

    # ========================================================
    # MOUTH OPEN FEATURE
    #
    # Mouth Aspect Ratio
    # ========================================================

    def get_mouth_feature(self, landmarks):

        mouth_height = self.distance(
            landmarks[self.MOUTH_TOP],
            landmarks[self.MOUTH_BOTTOM]
        )

        mouth_width = self.distance(
            landmarks[self.MOUTH_LEFT],
            landmarks[self.MOUTH_RIGHT]
        )

        if mouth_width <= 0:

            return 0.0

        return (
            mouth_height
            /
            mouth_width
        )

    # ========================================================
    # EYE OPEN FEATURE
    #
    # Average vertical eye opening normalized by
    # horizontal eye width.
    # ========================================================

    def get_eye_feature(self, landmarks):

        left_eye_height = self.distance(
            landmarks[self.LEFT_EYE_TOP],
            landmarks[self.LEFT_EYE_BOTTOM]
        )

        left_eye_width = self.distance(
            landmarks[self.LEFT_EYE_LEFT],
            landmarks[self.LEFT_EYE_RIGHT]
        )

        right_eye_height = self.distance(
            landmarks[self.RIGHT_EYE_TOP],
            landmarks[self.RIGHT_EYE_BOTTOM]
        )

        right_eye_width = self.distance(
            landmarks[self.RIGHT_EYE_LEFT],
            landmarks[self.RIGHT_EYE_RIGHT]
        )

        if (
            left_eye_width <= 0
            or
            right_eye_width <= 0
        ):

            return 0.0

        left_ratio = (
            left_eye_height
            /
            left_eye_width
        )

        right_ratio = (
            right_eye_height
            /
            right_eye_width
        )

        return (
            left_ratio
            +
            right_ratio
        ) / 2.0

    # ========================================================
    # EXTRACT ALL FEATURES
    # ========================================================

    def extract_features(self, landmarks):

        return {
            "smile": self.get_smile_feature(
                landmarks
            ),

            "eyebrow": self.get_eyebrow_feature(
                landmarks
            ),

            "mouth": self.get_mouth_feature(
                landmarks
            ),

            "eye": self.get_eye_feature(
                landmarks
            ),

            "frown": self.get_frown_feature(
                landmarks
            ),
        }

    # ========================================================
    # CALIBRATION
    # ========================================================

    def calibrate(self, features):

        if self.neutral_smile is None:

            self.neutral_smile = (
                features["smile"]
            )

            self.neutral_eyebrow = (
                features["eyebrow"]
            )

            self.neutral_mouth = (
                features["mouth"]
            )

            self.neutral_eye = (
                features["eye"]
            )

            self.neutral_frown = (
                features["frown"]
            )

        else:

            count = self.calibration_frames

            self.neutral_smile = (
                self.neutral_smile * count
                +
                features["smile"]
            ) / (count + 1)

            self.neutral_eyebrow = (
                self.neutral_eyebrow * count
                +
                features["eyebrow"]
            ) / (count + 1)

            self.neutral_mouth = (
                self.neutral_mouth * count
                +
                features["mouth"]
            ) / (count + 1)

            self.neutral_eye = (
                self.neutral_eye * count
                +
                features["eye"]
            ) / (count + 1)

            self.neutral_frown = (
                self.neutral_frown * count
                +
                features["frown"]
            ) / (count + 1)

        self.calibration_frames += 1

    # ========================================================
    # CALIBRATION STATUS
    # ========================================================

    def is_calibrated(self):

        return (
            self.calibration_frames
            >= EXPRESSION_CALIBRATION_FRAMES
        )

    # ========================================================
    # DETECT EXPRESSION
    # ========================================================

    def detect(self, landmarks):

        features = self.extract_features(
            landmarks
        )

        # ----------------------------------------------------
        # Calibration
        # ----------------------------------------------------

        if not self.is_calibrated():

            self.calibrate(
                features
            )

            self.current_expression = (
                "CALIBRATING"
            )

            return {
                "expression": "CALIBRATING",
                "smile_score": 0.0,
                "eyebrow_score": 0.0,
                "mouth_open_score": 0.0,
                "frown_score": 0.0,
                "eye_score": 0.0,
                "calibration_progress": (
                    self.calibration_frames
                    /
                    EXPRESSION_CALIBRATION_FRAMES
                ),
            }

        # ----------------------------------------------------
        # Smooth all features
        # ----------------------------------------------------

        self.smoothed_smile = self.smooth(
            self.smoothed_smile,
            features["smile"],
            EXPRESSION_EMA_ALPHA
        )

        self.smoothed_eyebrow = self.smooth(
            self.smoothed_eyebrow,
            features["eyebrow"],
            EXPRESSION_EMA_ALPHA
        )

        self.smoothed_mouth = self.smooth(
            self.smoothed_mouth,
            features["mouth"],
            EXPRESSION_EMA_ALPHA
        )

        self.smoothed_eye = self.smooth(
            self.smoothed_eye,
            features["eye"],
            EXPRESSION_EMA_ALPHA
        )

        self.smoothed_frown = self.smooth(
            self.smoothed_frown,
            features["frown"],
            EXPRESSION_EMA_ALPHA
        )

        # ----------------------------------------------------
        # Calculate changes from neutral
        # ----------------------------------------------------

        smile_change = (
            self.smoothed_smile
            -
            self.neutral_smile
        )

        eyebrow_change = (
            self.smoothed_eyebrow
            -
            self.neutral_eyebrow
        )

        mouth_change = (
            self.smoothed_mouth
        )

        eye_change = (
            self.smoothed_eye
            -
            self.neutral_eye
        )

        frown_change = (
            self.smoothed_frown
            -
            self.neutral_frown
        )

        # ====================================================
        # EXPRESSION CLASSIFICATION
        #
        # Priority is important.
        # ====================================================

        # ----------------------------------------------------
        # SURPRISE
        #
        # Raised eyebrows
        # + wider eyes
        # + open mouth
        # ----------------------------------------------------

        if (
            eyebrow_change
            >= SURPRISE_EYEBROW_THRESHOLD
            and
            eye_change
            >= SURPRISE_EYE_THRESHOLD
            and
            mouth_change
            >= SURPRISE_MOUTH_THRESHOLD
        ):

            detected = "SURPRISE"

        # ----------------------------------------------------
        # MOUTH OPEN
        # ----------------------------------------------------

        elif (
            mouth_change
            >= MOUTH_OPEN_THRESHOLD
        ):

            detected = "MOUTH_OPEN"

        # ----------------------------------------------------
        # SMILE
        # ----------------------------------------------------

        elif (
            smile_change
            >= SMILE_THRESHOLD
            and
            frown_change
            < FROWN_THRESHOLD
        ):

            detected = "SMILE"

        # ----------------------------------------------------
        # FROWN
        # ----------------------------------------------------

        elif (
            frown_change
            >= FROWN_THRESHOLD
        ):

            detected = "FROWN"

        # ----------------------------------------------------
        # EYEBROW RAISE
        # ----------------------------------------------------

        elif (
            eyebrow_change
            >= EYEBROW_THRESHOLD
        ):

            detected = "EYEBROW_RAISE"

        # ----------------------------------------------------
        # NEUTRAL
        # ----------------------------------------------------

        else:

            detected = "NEUTRAL"

        # ====================================================
        # TEMPORAL STABILITY
        # ====================================================

        if (
            detected
            ==
            self.previous_expression
        ):

            self.expression_frames += 1

        else:

            self.previous_expression = (
                detected
            )

            self.expression_frames = 1

        # ----------------------------------------------------
        # Accept expression only after stable frames
        # ----------------------------------------------------

        if (
            self.expression_frames
            >= EXPRESSION_STABLE_FRAMES
        ):

            self.current_expression = (
                detected
            )

        # ====================================================
        # RETURN RESULTS
        # ====================================================

        return {
            "expression": (
                self.current_expression
            ),

            "smile_score": (
                smile_change
            ),

            "eyebrow_score": (
                eyebrow_change
            ),

            "mouth_open_score": (
                mouth_change
            ),

            "frown_score": (
                frown_change
            ),

            "eye_score": (
                eye_change
            ),

            "calibration_progress": 1.0,
        }

    # ========================================================
    # RESET
    # ========================================================

    def reset(self):

        self.calibration_frames = 0

        self.neutral_smile = None

        self.neutral_eyebrow = None

        self.neutral_mouth = None

        self.neutral_eye = None

        self.neutral_frown = None

        self.smoothed_smile = None

        self.smoothed_eyebrow = None

        self.smoothed_mouth = None

        self.smoothed_eye = None

        self.smoothed_frown = None

        self.previous_expression = "NEUTRAL"

        self.expression_frames = 0

        self.current_expression = (
            "CALIBRATING"
        )