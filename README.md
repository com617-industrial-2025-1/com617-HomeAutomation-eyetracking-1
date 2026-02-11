# Assistive Eye & Head Tracking Home Automation

An accessibility-focused home automation controller designed for users with limited motor function. This system uses **eye gaze**, **head movements**, and **blink detection** to control home devices via openHAB, Velbus, and MQTT.

## 🚀 Features

- **Fluid Gaze Tracking**: Optimized MediaPipe iris tracking combined with head pose for intuitive control.
- **Smart Interaction**: 3-second dwell activation, blink confirmation, and head nod/shake gestures.
- **AI-Powered Routines**: Integrated Gemini LLM for context-aware routines (e.g., "Bedtime").
- **Caregiver Dashboard Integration**: MQTT logging of all user actions and emergency alerts.
- **Cross-Platform**: Runs on Windows, Linux, and Raspberry Pi.

---

## 🛠 Setup & Installation

### Option 1: Local Environment (Recommended for GUI)

1. **Python 3.12+** is required.
2. **Setup Virtual Environment**:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```
3. **Install Dependencies**:
   ```bash
   pip install -r src/requirements.txt
   ```
4. **Configure**:
   Edit `src/config.yaml` with your openHAB URL and Gemini API Key.
5. **Run**:
   ```bash
   python src/main.py
   ```

### Option 2: Docker (Best for Headless / Testing)

1. **Run Tests**:
   ```bash
   docker build -t eyetracker .
   docker run eyetracker
   ```
2. **Run Stack (App + MQTT)**:
   ```bash
   docker-compose up -d
   ```

### Option 3: VS Code Dev Containers
Open the project folder in VS Code and click **"Reopen in Container"**. All dependencies, including system libraries for MediaPipe, will be pre-installed.

---

## 📖 How to Use

- **Gaze**: Stare at a zone (e.g., "Light") for 3 seconds to trigger.
- **Confirm**: Long blink (0.5s) or a small head nod.
- **Cancel**: Eye blink or a head shake.
- **AI Routines**: Looking at "🌙 Bedtime" triggers a context-aware sequence of commands.

---

## 🧪 Testing
Run the automated test suite (47 tests):
```bash
cd src
python -m unittest discover -s tests -v
```

## 🏗 Architecture
- **MediaPipe**: For high-fidelity face and iris tracking.
- **openHAB**: The core home automation server.
- **Google Gemini**: Background reasoning for smart routines.
- **Paho-MQTT**: Communication with external monitoring tools.

---

## 📄 License
This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.