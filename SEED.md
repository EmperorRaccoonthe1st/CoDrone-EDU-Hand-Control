# Project Context: CoDrone Edu Computer Vision Controller

## 1. Project Overview
A Python-based application that uses a single webcam and Google MediaPipe to control a CoDrone Edu via body movements and dual-hand gestures. The architecture separates computer vision processing from drone hardware communication using multithreading and a thread-safe Singleton state machine.

## 2. Environment & Dependencies
* **Target OS:** Cross-platform (Windows & Arch Linux compatibility required).
* **Python Version:** Python >= 3.12 (Requires virtual environment isolation).
* **Core Libraries:**
  * `opencv-python` (cv2)
  * `mediapipe==0.10.21` *(CRITICAL: Must strictly use this older version).*
  * `codrone_edu` (Integrated via background worker thread).

## 3. Core Architecture
### 3.1. Dual-Hand Control Scheme
* **Left Hand (Speed Presets & Safe Landing):**
  * Closed Fist: Hover (0% translation speed).
  * 1 Finger Up (Index): Speed Preset 1 (25%).
  * 2 Fingers Up (Index + Middle): Speed Preset 2 (50%).
  * 3 Fingers Up (Index + Middle + Ring): Speed Preset 3 (75%).
  * 4 Fingers Up (Index + Middle + Ring + Pinky): Speed Preset 4 (100%).
  * Thumb Down (Fist): Safe Land command (initiates safe landing sequence).
* **Right Hand (Launch Gesture & 3D Virtual Joystick):**
  * **Point Up Gesture:** Initiates Takeoff / Launch from `SEARCHING` state. Can be repeated after landing.
  * **2-Second Takeoff Warmup Delay:** Upon launch, telemetry commands remain zeroed `(0, 0, 0, 0)` for 2.0 seconds while the drone stabilizes, before active joystick control begins.
  * **Thumbs Up Joystick Handle:** Active hand posture during `MANUAL_CONTROL`.
  * **Elevation / Throttle:** Screen height of right hand relative to screen center (screen Y = 0.5).
  * **Pitch:** Forward / Backward 3D tilt of the hand handle.
  * **Roll:** Left / Right sideways tilt of the hand handle.
  * **Yaw:** Rotational turn angle of the hand plane.

### 3.2. Project Structure
```
drone/
├── CommandCenter/         # Master Planning & Architectural Specs
│   ├── ARCHITECTURE.md
│   ├── SPEC.md
│   ├── PLAN.md
│   └── TESTING.md
├── state.py               # Singleton SystemState & DroneState
├── gestures.py            # Point Up launch, Left hand speed classifier & Thumbs Up joystick
├── telemetry.py           # Right hand 3D joystick pitch, roll, yaw, throttle mapper
├── vision.py              # Camera ingestion, 2-sec launch delay, MediaPipe & HUD overlay
├── drone_thread.py        # Background worker thread & Bluetooth/Mock dispatch
├── main.py                # Main application CLI entry point
├── fly.py                 # Standalone hardware test script
├── tests/                 # Automated Unit Test Suites
└── SEED.md
```
