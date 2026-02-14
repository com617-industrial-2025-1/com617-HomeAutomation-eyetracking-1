# Research Notes & Inspiration

During the development of this project, I explored several libraries, research papers, and existing repositories to find the best approach for webcam-based assistive technology.

## 📚 Inspiration Repositories
- **[MediaPipe Iris](https://github.com/google/mediapipe)**: The primary foundation for the eye landmarking logic. I used their iris-tracking papers to understand how to get metric-accurate pupil centers without specialized IR hardware.
- **[GazePointer](https://github.com/Tidiane/GazePointer)**: An inspiration for the calibration logic. Although I moved to a calibration-free zone-based system, GazePointer was crucial in understanding basic pupil tracking.
- **[WebGazer.js](https://github.com/brownhci/WebGazer)**: I studied their approach to using regression models for gaze estimation in the browser. It influenced my decision to use a simpler, more stable zone-based approach for my Python implementation.

## 📖 Key Research Papers
- **"Eye Tracking for Home Automation" (2020-2023)**: Various studies on IoT integration for paralyzed patients (e.g., using EEG or Eye tracking).
- **"The Midas Touch Problem in Gaze-Based Interfaces"**: A foundational concept in HCI. My implementation of "Dwell Time" (3 seconds in `config.yaml`) and "Blink-to-Confirm" is a direct response to this research.

## 🛠️ Tooling Evolution
- **OpenCV**: Started with version 4.8.0 for basic imaging.
- **MediaPipe**: Moved to the `0.10.x` Python API for better support of the `face_landmarker.task` bundle.
- **openHAB**: Selected over Home Assistant for its slightly more industrial focus and robust REST API documentation.
- **Gemini 2.0**: Integrated the latest LLM capabilities to allow natural language "Routines" rather than just hard-coded triggers.
