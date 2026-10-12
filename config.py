# ============================================================
# MULTIMODAL TOUCHLESS HCI ENGINE
# Configuration File
# ============================================================

# ---------------- CAMERA SETTINGS ----------------

CAMERA_INDEX = 0

CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CAMERA_FPS = 30


# ---------------- MEDIAPIPE SETTINGS ----------------

MAX_NUM_HANDS = 1

MODEL_COMPLEXITY = 0

MIN_DETECTION_CONFIDENCE = 0.70

MIN_TRACKING_CONFIDENCE = 0.70


# ---------------- CURSOR SETTINGS ----------------

# Dead-space around the camera frame.
# This prevents the cursor from getting stuck at
# the extreme screen edges.

CURSOR_MARGIN_X = 80
CURSOR_MARGIN_Y = 60


# EMA smoothing factor.
#
# Lower value  -> smoother but slower
# Higher value -> faster but less smooth

EMA_ALPHA = 0.35


# ---------------- GESTURE SETTINGS ----------------

# Normalized distance between thumb tip
# and index finger tip.

PINCH_DISTANCE = 0.055


# Minimum time between clicks.

CLICK_COOLDOWN = 0.35


# ---------------- SCROLL SETTINGS ----------------

# Minimum time between thumb-up/thumb-down
# scroll events.


# Scroll amount per detected gesture.

SCROLL_UP_SPEED = 10
SCROLL_DOWN_SPEED = 10
SCROLL_COOLDOWN = 0.25

# Number of consecutive frames required
# before accepting a scroll gesture.

SCROLL_STABLE_FRAMES = 5

# Smoothing factor for wrist rotation.

WRIST_EMA_ALPHA = 0.25


# ---------------- DISPLAY SETTINGS ----------------

SHOW_CAMERA = True

SHOW_LANDMARKS = True

SHOW_STATUS = True


#-------------------------------------------------------------------#

# ============================================================
# EYE BLINK / WINK SETTINGS
# ============================================================

# EAR below this value means the eye is considered closed.

EYE_CLOSED_THRESHOLD = 0.21

# Number of consecutive frames required to confirm a wink.

WINK_STABLE_FRAMES = 4

# Minimum time between eye-click events.

WINK_COOLDOWN = 0.60

# Enable actual mouse clicks.

ENABLE_EYE_CLICKS = True

# Camera display.

SHOW_EYE_CAMERA = True

# Draw eye landmarks.

SHOW_EYE_LANDMARKS = True

#----------------------------------------------------------------#

# ============================================================
# FACIAL EXPRESSION SETTINGS
# ============================================================

# ------------------------------------------------------------
# Calibration
# ------------------------------------------------------------

EXPRESSION_CALIBRATION_FRAMES = 90

# ------------------------------------------------------------
# Stability
# ------------------------------------------------------------

EXPRESSION_STABLE_FRAMES = 6

# ------------------------------------------------------------
# Feature smoothing
# ------------------------------------------------------------

EXPRESSION_EMA_ALPHA = 0.25

# ------------------------------------------------------------
# Smile
# ------------------------------------------------------------

SMILE_THRESHOLD = 0.035

# ------------------------------------------------------------
# Eyebrow raise
# ------------------------------------------------------------

EYEBROW_THRESHOLD = 0.018

# ------------------------------------------------------------
# Mouth open
# ------------------------------------------------------------

MOUTH_OPEN_THRESHOLD = 0.055

# ------------------------------------------------------------
# Frown
# ------------------------------------------------------------

FROWN_THRESHOLD = 0.025

# ------------------------------------------------------------
# Surprise
# ------------------------------------------------------------

SURPRISE_EYEBROW_THRESHOLD = 0.030

SURPRISE_EYE_THRESHOLD = 0.018

SURPRISE_MOUTH_THRESHOLD = 0.045

# ------------------------------------------------------------
# Camera
# ------------------------------------------------------------

SHOW_EXPRESSION_CAMERA = True

SHOW_EXPRESSION_LANDMARKS = True


#-------------------------@@@@@@@@@@@@@@------------------------------#

# ============================================================
# VOICE COMMAND SETTINGS
# ============================================================

VOICE_SAMPLE_RATE = 16000

VOICE_CHANNELS = 1

VOICE_MODEL = "base"

VOICE_MIN_RECORDING_SECONDS = 0.30

VOICE_MAX_RECORDING_SECONDS = 8.0

VOICE_LANGUAGE = "en"

VOICE_INPUT_DEVICE = None

VOICE_EXECUTE_COMMANDS = True


# ============================================================
# OCR / SCREEN READER SETTINGS
# ============================================================

# Common Windows Tesseract location.
# The OCR engine will also automatically search
# alternative locations.

TESSERACT_PATH = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

# OCR language

OCR_LANGUAGE = "eng"

# Minimum OCR confidence to keep detected text.

OCR_MIN_CONFIDENCE = 35

# Maximum characters sent to speech at once.
# Prevents extremely long pages from being spoken
# as one huge sentence.

TTS_MAX_CHARACTERS = 3000

# Speech settings

TTS_RATE = 150

TTS_VOLUME = 1.0

TTS_VOICE_NAME = "Microsoft Zira Desktop"

OCR_SCREENSHOT_DELAY = 0.2

SHOW_OCR_WINDOW = True

# ============================================================
# OCR SCREEN REGION
# ============================================================

OCR_CROP_TOP = 115

OCR_CROP_BOTTOM = 45

OCR_CROP_LEFT = 15

OCR_CROP_RIGHT = 15

# ============================================================
# SELECTIVE OCR SETTINGS
# ============================================================

# Default OCR mode
OCR_MODE = "FULL_SCREEN"

# Minimum size of a selectable region
OCR_MIN_REGION_WIDTH = 50
OCR_MIN_REGION_HEIGHT = 30

# Selection window title
OCR_SELECTION_WINDOW_TITLE = "Select OCR Region"

# Mouse selection behavior
OCR_SELECTION_LINE_THICKNESS = 2

# ============================================================
# AI SETTINGS
# ============================================================

# Default AI provider.
#
# Valid values:
# "ollama"
# "gemini"
#
# Ollama is local/offline.
AI_PROVIDER = "ollama"

# ------------------------------------------------------------
# Ollama
# ------------------------------------------------------------

OLLAMA_HOST = "http://localhost:11434"

OLLAMA_MODEL = "llama3.2"

# ------------------------------------------------------------
# Gemini
# ------------------------------------------------------------

GEMINI_API_KEY = None

GEMINI_MODEL = "gemini-3.8-flash"
GEMINI_FALLBACK_MODEL = "gemini-3.7-flash"

# ------------------------------------------------------------
# Gemini retry settings
# ------------------------------------------------------------

GEMINI_RETRY_ATTEMPTS = 2

GEMINI_RETRY_DELAY = 1.5

# ------------------------------------------------------------
# AI generation
# ------------------------------------------------------------

AI_MAX_INPUT_CHARACTERS = 12000

AI_MAX_OUTPUT_TOKENS = 800

AI_TEMPERATURE = 0.2

# ============================================================
# AI SCREEN READER SETTINGS
# ============================================================

AI_SCREEN_TARGET_LANGUAGE = "Kannada"

AI_SCREEN_TTS = True

AI_SCREEN_MODE = "SELECTED"