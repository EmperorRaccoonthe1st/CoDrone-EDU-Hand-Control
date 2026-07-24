# Project Context: CoDrone Edu Computer Vision Controller

## 1. Project Overview
A Python-based application that uses a single webcam and Google MediaPipe to control a CoDrone Edu via body movements and hand gestures. The architecture separates computer vision processing from drone hardware communication using multithreading and a thread-safe Singleton state machine.

## 2. Environment & Dependencies
* **Target OS:** Cross-platform (Windows & Arch Linux compatibility required).
* **Editor/Workflow:** VS Code with Vim emulation; terminal-centric development.
* **Python Version:** Python 3.12 (Requires virtual environment isolation).
* **Core Libraries:**
  * `opencv-python` (cv2)
  * `mediapipe==0.10.21` *(CRITICAL: Must strictly use this older version. Newer versions >=0.10.31 deprecated the `mp.solutions` API in favor of the Tasks API. Do not update MediaPipe).*
  * `codrone_edu` (Pending implementation).

## 3. Core Architecture
### 3.1. State Machine & Shared Memory (`DroneState`)
Data is shared between the Vision Thread (Main) and the Drone Hardware Thread (Background) using a thread-safe Singleton guarded by `threading.Lock()`.
* **Enums (`SystemState`):** `INIT`, `SEARCHING`, `MANUAL_CONTROL`, `EMERGENCY_STOP`.
* **Flight Telemetry Variables:** `roll`, `pitch`, `yaw`, `throttle` (Integers ranging from -100 to 100).

### 3.2. Camera Initialization Pipeline
Uses a custom `initialize_camera()` function that forcefully bypasses the default MSMF backend on Windows to prevent silent infinite hangs during `cap.read()`.
* **Windows:** Enforces `cv2.CAP_DSHOW` (DirectShow).
* **Linux:** Enforces `cv2.CAP_V4L2`.
* Includes hardware warm-up delays and iterative index fallback for virtual camera interference.

## 4. Current Implemented Logic (Vision Thread)
The main `vision_loop()` successfully extracts 3D hand landmarks via MediaPipe and processes them against the state machine. The video feed is horizontally mirrored for a natural UX.

### 4.1. Active Features & Gestures
* **Visual Debugger & Overlay:** Uses OpenCV to draw MediaPipe skeletons, bounding boxes, handedness labels directly on the wrists, and dynamic colored text indicating the current `SystemState`.
* **Debounced Killswitch (Crossed Arms):**
  * Compares the X-coordinates of `wrists["Left"]` and `wrists["Right"]`.
  * If the left wrist crosses over the right wrist for 10 consecutive frames (~0.3s), the system forcefully locks into `EMERGENCY_STOP`.
  * Ignores 1-frame MediaPipe handedness classification glitches.
* **Unlock / Takeoff (Point Gesture Recognizer):**
  * Transitions state from `SEARCHING` to `MANUAL_CONTROL`.
  * Utilizes a dedicated `is_pointing()` boolean function.
  * Validates that the Index finger tip (Node 8) is extended above its PIP joint (Node 6), while the Middle (12), Ring (16), and Pinky (20) tips are folded strictly below their respective PIP joints (Nodes 10, 14, 18).
* **Keyboard Overrides:**
  * `q`: Instantly triggers `EMERGENCY_STOP` and safely breaks the vision loop.
  * `r`: Manually resets the state from `EMERGENCY_STOP` back to `SEARCHING`.

## 5. Immediate Next Steps (WIP)
1. **Telemetry Mapping:** Map the spatial coordinates/angles of the right hand's Point Gesture to output precise integer vectors (-100 to 100) for the `DroneState`'s pitch, roll, yaw, and throttle variables.
2. **Drone Worker Thread:** Implement the secondary `threading.Thread` to initialize the `codrone_edu` SDK, read the `DroneState` Singleton at a fixed tick rate, and transmit Bluetooth flight commands.