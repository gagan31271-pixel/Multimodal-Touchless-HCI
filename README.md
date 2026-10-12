# Multimodal Touchless Human-Computer Interaction Engine

A multimodal human-computer interaction system designed to make computer control more natural and accessible using **hand gestures, eye movements, voice commands, and screen-aware AI**.

The project combines computer vision, speech processing, and AI-powered screen analysis to provide alternative ways to interact with a computer without relying entirely on a traditional mouse and keyboard.

## Overview

Traditional computer interaction primarily depends on physical input devices such as a mouse and keyboard. This project explores how multiple input modalities can work together to provide a more flexible, touchless interaction experience.

The system integrates hand gesture recognition, eye and blink detection, voice commands, screen text extraction, and face-based authentication into a unified application.

The application includes a Streamlit-based user dashboard for accessing its interaction features.

## Key Features

### 1. Hand Gesture Mouse Control

* Detects hand landmarks using computer vision.
* Interprets supported hand gestures for mouse interaction.
* Supports gesture-based cursor movement and configured mouse actions.
* Uses cursor smoothing to improve control stability.

### 2. Eye and Blink Interaction

* Analyzes eye landmarks and blink-related movements.
* Includes eye interaction functionality such as wink detection.
* Provides an alternative interaction method using eye movements.

### 3. Voice Command System

* Supports configured voice commands for computer interaction.
* Includes a speech-processing and dictation component.
* Uses command-processing modules to connect recognized commands with application actions.

### 4. Screen AI and OCR

* Extracts visible text from screen content using OCR.
* Provides screen-reading and context-related processing functionality.
* Includes context-action functionality for interacting with extracted screen information.

### 5. Face-Based Authentication

* Provides a face-registration and verification workflow.
* Uses DeepFace for face verification.
* Uses a registered face image and authentication configuration for the current prototype.

**Security note:** This is a prototype authentication mechanism, not a replacement for operating-system authentication or production-grade security. Its security depends on the verification configuration and implementation.

### 6. Unified Dashboard

* Provides a central interface for accessing interaction features.
* Organizes the system's different modules.
* Includes performance-related telemetry and runtime monitoring functionality.

## Technology Stack

| Technology                  | Purpose                                    |
| --------------------------- | ------------------------------------------ |
| Python                      | Core application development               |
| OpenCV                      | Image and video processing                 |
| MediaPipe                   | Hand and facial landmark detection         |
| DeepFace                    | Face verification                          |
| Streamlit                   | Interactive dashboard                      |
| OCR libraries               | Screen text extraction                     |
| Speech-processing libraries | Voice interaction and dictation            |
| PyAutoGUI                   | Computer input automation where configured |
| NumPy                       | Numerical and image-data processing        |

The exact dependencies are listed in `requirements.txt`.

## Project Structure

```text
Multimodal-Touchless-HCI/
├── config/
│   └── context_profiles.yaml
├── data/
│   └── face_auth/                 # Private local authentication data
├── literature/
│   ├── Papers/                    # Research papers
│   ├── Final Project Synopsis.docx
│   └── Synopsis.pdf
├── modules/
│   ├── context_switcher/
│   ├── face_analysis/
│   ├── hand_gesture/
│   ├── multimodal/
│   ├── ocr_screen/
│   ├── security/
│   ├── voice_command/
│   ├── ai_engine.py
│   ├── ai_screen_processor.py
│   └── speech_engine.py
├── tests/
├── utils/
│   └── telemetry.py
├── .gitignore
├── config.py
├── dashboard.py
├── main.py
├── mode_runner.py
├── requirements.txt
└── user_dashboard.py
```

The `data/face_auth/` directory is intended for private local authentication data and should not be committed to a public repository.

## Prerequisites

Before running the application, make sure you have:

* Python 3.12, matching the development environment used for this project.
* Git.
* A webcam for hand, eye, and face-based features.
* A microphone for voice interaction.
* Windows or another environment compatible with the configured input and camera libraries.

Some functionality may require additional operating-system permissions or configuration.

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/gagan31271-pixel/Multimodal-Touchless-HCI.git
cd Multimodal-Touchless-HCI
```

### 2. Create a virtual environment

On Windows:

```bash
python -m venv venv
```

Activate it in Git Bash:

```bash
source venv/Scripts/activate
```

Alternatively, activate it in Command Prompt:

```cmd
venv\Scripts\activate
```

### 3. Install dependencies

Upgrade pip:

```bash
python -m pip install --upgrade pip
```

Install the project dependencies:

```bash
pip install -r requirements.txt
```

Some packages may require additional system libraries, hardware permissions, or platform-specific setup.

## Running the Application

### Main user dashboard

From the project root, activate the virtual environment and run:

```bash
streamlit run user_dashboard.py
```

Streamlit should provide a local URL in the terminal. Open that URL in your browser.

### Alternative entry points

The repository also contains:

* `main.py` — main application entry point.
* `dashboard.py` — performance dashboard.
* `mode_runner.py` — interaction-mode execution support.

Use the entry point appropriate to the functionality you want to test. The primary user interface is `user_dashboard.py`.

## Face Authentication

The project includes a face-based authentication workflow.

In the current implementation, authentication data is stored locally under:

```text
data/face_auth/
```

The directory may contain a registered face image and authentication configuration.

For privacy, this data is excluded from version control. A fresh clone therefore will not contain your locally registered face.

If face authentication is enabled, complete the registration process locally before using the authentication-protected dashboard.

Do not upload biometric images, authentication data, API keys, or passwords to a public repository.

## Testing

The `tests/` directory contains tests for selected application components, including:

* Face authentication.
* Screen processing and OCR functionality.
* Voice-command processing.
* AI-related functionality.
* Face and blink analysis.

Activate the virtual environment before running tests.

To run the test suite with pytest, if pytest is installed:

```bash
python -m pytest
```

Individual tests can also be run when debugging a specific component.

## Research and Documentation

The `literature/` directory contains project documentation and research material related to human-computer interaction, hand gesture recognition, multimodal interaction, and related topics.

These materials support the project's academic background and development.

## Current Scope and Limitations

This project is an ongoing academic prototype. Its behavior depends on the implemented modules, hardware, environment, and configuration.

Potential limitations include:

* Accuracy may vary with lighting, camera quality, and user positioning.
* Gesture and eye interaction may require calibration or practice.
* Voice recognition may be affected by background noise and microphone quality.
* OCR accuracy depends on screen content and text visibility.
* Face authentication should not be treated as production-grade security.
* Some modules may require additional platform-specific configuration.

## Future Enhancements

Possible future improvements include:

* More robust multimodal input coordination.
* Improved gesture recognition and cursor stability.
* Better handling of conflicting input modalities.
* Expanded voice-command support.
* More comprehensive accessibility features.
* Improved authentication security and liveness detection.
* Performance evaluation across different environments and users.
* Automated testing and installation improvements.

## Privacy and Security

This project interacts with webcam, microphone, screen content, and computer input functionality.

Users should understand which permissions are enabled before running it.

Never commit the following to a public repository:

* API keys or access tokens.
* Passwords or private credentials.
* Registered face images or biometric data.
* Personal authentication configuration.
* Private environment-variable files.

Review `.gitignore` and inspect staged files before every commit.


Project: [Multimodal-Touchless-HCI](https://github.com/gagan31271-pixel/Multimodal-Touchless-HCI)

---

Developed as an academic project exploring multimodal, touchless human-computer interaction.
