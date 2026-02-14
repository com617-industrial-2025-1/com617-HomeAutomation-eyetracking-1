# Development Journey: Assistive Eye-Tracking Home Control

This document outlines my journey in researching, designing, and implementing this assistive technology project.

## 🕒 Phase 1: Identifying the Problem & Research
I started this project with a goal: creating a hands-free interaction system for individuals with motor disabilities. Hand-based interfaces (mice, keyboards, touchscreens) are often inaccessible, so I pivoted to **Eye Tracking**.

**Key Research Points:**
- I studied **Video Oculography (VOG)** techniques.
- I looked at existing open-source projects like **GazePointer** and **WebGazer.js** to understand how they map pupil location to screen coordinates.
- I read research papers on the **Midas Touch problem**—the challenge of distinguishing between "just looking" and "intending to interact." This led me to implement **Dwell Time** as a primary trigger mechanism.

## 🛠️ Phase 2: Prototyping with OpenCV
My first attempt involved using pure OpenCV with Haar Cascades for eye detection. However, I found it extremely sensitive to lighting and head movement.

**Lessons Learned:**
- Standard pupil-center-corneal-reflection (PCCR) requires infrared hardware for high accuracy.
- Webcam-only tracking needs a more robust landmarking approach.

## 🚀 Phase 3: Moving to MediaPipe Face Mesh
I decided to use **MediaPipe's Face Landmarker** (468 points). This was a game-changer because it provides stabilized landmarks for the iris and eye contours.

**Design Decisions:**
- I implemented **Relative Gaze Mapping**: instead of trying to hit 1-pixel accuracy (which is impossible with a 720p webcam), I divided the screen into large interaction **Zones**.
- This "Zone-based" approach makes the system incredibly reliable even with significant head movement.

## 🏠 Phase 4: Smart Home Integration
I wanted the system to actually *do* something. I chose **openHAB** as the backend because of its mature REST API and wide device support.

**Technical Hurdles:**
- Integrating multiple protocols. I added **MQTT** for lightweight logging and real-time status updates.
- I also implemented a **Velbus** client for high-end industrial automation scenarios.

## 🧠 Phase 5: Adding Intelligence (Gemini AI)
Single actions (Light ON/OFF) are simple, but real life is complex. I integrated **Google Gemini 2.0 Flash** to handle "Routines."
- **Example:** Looking at the "Bedtime" zone doesn't just turn off a light; the AI handles a sequence: checking the time, dimming the light, closing the blinds, and sending a status update to the caregiver via MQTT.

## ✨ Phase 6: Refinement & Gestures
To solve the Midas Touch problem further, I added **Gesture Recognition**:
- **Blink-to-Confirm**: Users can look at a zone and blink to confirm immediately, bypassing the dwell timer.
- **Nod/Shake**: Added as additional input channels for future expansion.

## 🏁 Conclusion
The journey from a simple "detect eye" script to a full AI-integrated home control system has been a massive learning experience in computer vision, HCI (Human-Computer Interaction), and IoT.
