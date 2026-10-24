Overview

The Multimodal Touchless Human-Computer Interaction Engine
(Multimodal Touchless HCI) lets users interact with a computer through
touch-free input methods. It provides separate interaction modes and a
shared Screen AI feature for extracting, reading, translating, and
summarizing on-screen text.

The current application flow includes face authentication, a user
dashboard, and the available interaction features. Screen AI is designed
to remain accessible alongside the selected interaction mode.

Key Features

1. Face Authentication

Uses face verification as an access gate before opening the
dashboard.

Uses DeepFace with the FaceNet512 model for face matching.

Keeps face-authentication data in the local data/face_auth/
directory.

Keep biometric data private; do not commit it to Git.

2. Hand Gesture Mouse

Gesture                         Action

Index finger                    Move cursor
Index + middle fingers          Left click
Index + middle + ring fingers   Right click
Index + little finger           Drag
Thumb                           Scroll up
Thumb + little finger           Scroll down
Fist                            Neutral / no action

Cursor smoothing helps reduce sudden movement.

3. Eye / Wink Control

Left-eye wink: left click.

Right-eye wink: right click.

Closing both eyes should not trigger a mouse click.

Stability checks and a cooldown help reduce accidental repeated
actions.

4. MAX Voice Assistant

MAX supports voice-driven computer actions such as application launching
and closing, browser searches, and other configured system commands.

Voice Typing / Dictation

The separate dictation engine uses Whisper for speech transcription and
SoundDevice for microphone input. Recognized speech is typed into the
active application.

Supported controls: - Start typing --- starts voice typing and
confirms that typing mode has started. - Stop typing --- stops voice
typing and confirms that typing mode has stopped. - Pause typing ---
temporarily pauses dictation. - Resume typing --- continues
dictation. - New line / New paragraph --- inserts line breaks. -
Delete that --- attempts to undo the previous dictated text.

The dictation engine handles controls while it owns the microphone.
MAX's regular command listener pauses during active dictation and
resumes when dictation ends.

5. Screen AI (Shared Feature)

Screen AI can be used alongside the selected interaction mode: - Capture
the screen or select a screen region. - Extract text using Tesseract OCR
through pytesseract. - Read extracted text aloud using
text-to-speech. - Translate selected text using the configured AI
engine. - Summarize selected text using the configured AI engine. -
Report OCR information such as word count and confidence where
available.

6. AI Processing

The AI engine uses a provider fallback design: - Google Gemini is
tried first for translation. - Ollama with a locally installed model
can be used as a fallback. - Summarization and other configured
text-generation tasks use the AI engine's supported provider workflow.

Provider availability, network connectivity, API configuration, and the
local Ollama model affect response time. Keep API credentials in
environment variables and never commit them.

7. Dashboard

The Streamlit user dashboard provides the main interface for
authentication, interaction modes, and shared Screen AI features.

Technology Stack

Language: Python 3.12

Dashboard: Streamlit

Computer vision: OpenCV, MediaPipe

Face verification: DeepFace, FaceNet512

Mouse and keyboard automation: PyAutoGUI

Voice commands: SpeechRecognition

Dictation / speech-to-text: OpenAI Whisper, SoundDevice

Text-to-speech: pyttsx3 (where configured)

OCR: Tesseract OCR, pytesseract

AI processing: Google Gemini API, Ollama

Numerical processing: NumPy

Configuration / secrets: environment variables, python-dotenv
(where configured)

Project Structure

The repository is organized into modules. Some files may differ as
development continues.

Multimodal-Touchless-HCI/
├── config/                         # Configuration files
├── data/
│   └── face_auth/                  # Local face-authentication data (private)
├── literature/                     # Literature survey and project references
├── modules/
│   ├── ai_engine.py                # AI provider and text-processing logic
│   ├── ai_screen_processor.py      # Screen AI processing workflow
│   ├── context_switcher/            # Application-context support
│   ├── face_analysis/               # Face and eye analysis
│   ├── hand_gesture/                # Hand tracking and gesture control
│   ├── multimodal/
│   │   └── screen_service.py        # Shared screen interaction service
│   ├── ocr_screen/                  # Screen capture and OCR
│   ├── security/                    # Authentication-related components
│   └── voice_command/
│       ├── max.py                   # MAX voice assistant
│       └── dictation_engine.py      # Whisper-based voice typing
├── tests/                           # Tests
├── utils/                           # Shared utilities
├── mode_runner.py                   # Interaction mode runner
├── user_dashboard.py                # User dashboard
└── requirements.txt                 # Python dependencies

Treat the actual files in your local checkout as the source of truth;
the structure above is a guide to the main components.

Requirements

Windows is the primary development environment.

Python 3.12 is recommended.

A webcam for face authentication and camera-based interaction modes.

A microphone for MAX and voice typing.

Speakers or headphones for spoken feedback.

Internet access for Gemini API requests.

Ollama installed locally if you want to use the local-model
fallback.

Tesseract OCR installed and available to pytesseract.

External dependencies

Tesseract OCR: Install the Tesseract OCR engine. If it is not
detected automatically, configure its executable path in the
project.

Ollama: Install Ollama and download a model supported by your
configuration. The configured model name must match the installed
model.

Gemini API: Create an API key and store it in the environment
variable expected by your configuration. Never place the key
directly in source code or commit it.

Setup

1. Clone the repository

git clone https://github.com/gagan31271-pixel/Multimodal-Touchless-HCI.git
cd Multimodal-Touchless-HCI

2. Create and activate a virtual environment

Windows PowerShell:

py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1

Windows Command Prompt:

py -3.12 -m venv .venv
.venv\Scripts\activate.bat

3. Install Python dependencies

python -m pip install --upgrade pip
pip install -r requirements.txt

If a dependency fails to install, confirm that the active interpreter is
Python 3.12 and follow that dependency's platform-specific installation
instructions.

4. Configure environment variables

If your project configuration uses python-dotenv, create a local
.env file and add the Gemini key using the exact variable name
expected by your code. For example:

GEMINI_API_KEY=your_api_key_here

The variable name may differ in your checkout. Never commit .env or
real API credentials.

5. Prepare face authentication

Follow the project's face-authentication workflow to enroll or configure
an authorized face. Keep the resulting data in data/face_auth/ and
verify that the directory is covered by .gitignore.

6. Start the application

From the project root, run:

streamlit run user_dashboard.py

If your checkout uses a different launcher, use the launch command
defined by that version of the project.

How to Use

Start the Streamlit application.

Complete face authentication.

Open the user dashboard.

Select the interaction mode:

Hand Gesture

Eye / Wink

MAX / Voice

Use Screen AI alongside the selected mode to select screen content
and read, translate, or summarize extracted text.

For voice typing, focus the target application or text field before
saying "Start typing." Say "Stop typing" when finished.

Important: PyAutoGUI types into the currently focused application.
Check the active window before dictating or issuing commands that
control the mouse or keyboard.

Privacy and Security

Do not commit .env files, API keys, credentials, or private
face-authentication data.

Keep data/face_auth/ local and verify that it is covered by
.gitignore.

Screen captures and OCR text may contain private information. Review
what is sent to external AI providers before using translation or
summarization.

Gemini requests require network access; local Ollama processing
depends on the installed model and local system resources.

Test automation commands before using them in applications
containing unsaved or sensitive work.

Troubleshooting

Camera is not detected

Close other applications that may be using the webcam.

Check Windows camera permissions.

Confirm that the correct camera device is selected.

Microphone or voice typing does not work

Check Windows microphone permissions and the default recording
device.

Confirm that SoundDevice can access the microphone.

Allow the Whisper model to finish loading.

Speak clearly and pause briefly so the engine can finish a speech
segment.

If "Stop typing" is not detected, check the terminal output for the
recognized transcript and dictation status messages.

OCR returns little or no text

Ensure Tesseract OCR is installed and discoverable.

Select a region with readable text and adequate contrast.

Accuracy depends on resolution, font size, and image quality.

Gemini translation is slow or unavailable

Check network access and API-key configuration.

Provider limits, retries, timeouts, and model availability can
affect latency.

Confirm that the configured Ollama fallback model is installed and
running if local fallback is enabled.

PyAutoGUI types into the wrong window

Click the intended application and place the cursor in the target
text field before starting dictation.

Stop typing before switching to another task.

Development Status

The project brings together face authentication, the dashboard, hand
gesture controls, eye/wink controls, MAX voice commands and dictation,
OCR-based screen reading, and AI-assisted translation and summarization.

The implementation continues to evolve. Features such as context-aware
application profiles, additional facial-expression actions, and broad
end-to-end validation should be considered complete only when verified
in the current codebase.

Contributing

Create a feature branch.

Keep changes focused on one module or feature.

Test the relevant interaction mode and check that existing modes
still work.

Never commit API credentials, private face-authentication data, or
personal screen captures.

Document new dependencies and setup requirements.

License

Add a license file and update this section if you intend to distribute
the project under a specific open-source license.