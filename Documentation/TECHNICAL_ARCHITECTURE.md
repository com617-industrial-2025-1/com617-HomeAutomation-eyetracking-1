# Technical Architecture & File Breakdown

This project is built with a modular architecture to separate input processing from home automation logic.

## 🏗️ System Overview
The system follows a classic **Sense -> Think -> Act** pipeline:
1. **Sense**: Capture camera frames and extract eye landmarks (MediaPipe).
2. **Think**: Map gaze to UI zones and detect interaction events (dwell/blink).
3. **Act**: Send commands to openHAB, Velbus, or MQTT.

---

## 📂 File Breakdown

### Root Components
- **`main.py`**: The orchestrator. Coordinates all modules, handles the main loop, and manages the UI overlay.

### `eye_tracking/`
- **`tracker.py`**: Handles the MediaPipe Face Landmarker. It extracts iris landmarks and calculates the normalized (0-1) gaze coordinates.
- **`gaze_mapper.py`**: Manages the interaction "Zones." It calculates dwell time and determines which zone the user is currently focused on.

### `interaction/`
- **`gesture_engine.py`**: A state machine for detecting gestures. It processes eye-opening ratios for blinks and head orientation for nods/shakes.

### `home_automation/`
- **`openhab_client.py`**: A clean wrapper for the openHAB REST API. Handles GET/POST requests for item states and commands.
- **`mqtt_client.py`**: Manages the connection to the MQTT broker. Publishes alerts and action logs for telemetry.
- **`velbus_client.py`**: Interface for Velbus home automation systems via serial communication.

### `ai/`
- **`assistant.py`**: Integration with **Gemini 2.0 Flash**. It uses structured prompts to interpret complex user goals (routines) and return a list of device actions in JSON format.

### `ui/`
- **`overlay.py`**: Responsible for the visual feedback. It draws the gaze point, zone boundaries, dwell progress bars, and status text onto the OpenCV frames.

---

## 🔄 Data Flow
1. **Camera** -> `EyeHeadTracker` -> `TrackerResult` (Gaze X, Y, Blink state).
2. `TrackerResult` -> `GazeMapper` -> `ActiveZone`.
3. `TrackerResult` -> `GestureEngine` -> `InteractionEvent` (e.g., BLINK).
4. `ActiveZone` + `InteractionEvent` -> `main.py` -> Trigger Action.
5. `main.py` -> `OpenHABClient` / `AIAssistant` -> **Physical Device Change**.
6. `main.py` -> `MQTTClient` -> **Telemetry Log**.
