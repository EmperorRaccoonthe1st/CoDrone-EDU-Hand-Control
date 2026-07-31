# CoDrone Edu Vision Controller

An ML-powered computer vision gesture flight controller for the **Robolink CoDrone Edu**, featuring **MediaPipe 3D Hand Landmark Tracking**, a **Virtual 3D Joystick**, and **Real-Time Telemetry Logging**.

![Visual HUD Overlay](https://img.shields.io/badge/UI-Professional_HUD_Overlay-blue?style=for-the-badge)
![MediaPipe](https://img.shields.io/badge/AI-MediaPipe_0.10.21-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10+-yellow?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

---

## Features

- **Dual-Hand Gesture Flight Control**:
  - **Right Hand Point Up**: Launch takeoff and calibrate neutral flight baselines.
  - **Right Hand Thumbs-Up Joystick**: 3D orientation tilt for Roll, Pitch, and Yaw translation.
  - **Left Hand Altitude Throttle**: Screen height controls vertical climb and descent.
  - **Left Hand Speed Presets**: Extend 1 to 4 fingers to select translation speed multipliers (25%, 50%, 75%, 100%).
  - **Left Hand Hover Pause**: Closed fist pauses translation for safe pilot re-orientation.
  - **Left Hand Safe Landing**: Thumb-Down fist lands the drone safely.
  - **Crossed Wrists Deadman Killswitch**: Crossing wrists in an "X" posture engages instant hardware motor shutdown.
- **Session Flight Monitoring & Frame Saver**:
  - Automatically records timestamped telemetry CSV logs and JPEG snapshot frames under `logs/session_YYYYMMDD_HHMMSS/`.

---

## Quick Start: Standalone Executable (Recommended)

Pre-compiled portable standalone binaries are available inside the `dist/` directory. No Python installation or package setup is required on the target machine.

### Running on Windows (`WIN_CoDroneVisionController.exe`)

1. Open Command Prompt or PowerShell in the `dist/` directory.
2. Launch standard flight mode:
   ```cmd
   dist\WIN_CoDroneVisionController.exe
   ```
3. Launch simulation / dry-run mode (no physical drone or camera required):
   ```cmd
   dist\WIN_CoDroneVisionController.exe --mock-drone --mock-camera
   ```
4. Launch with flight logging enabled:
   ```cmd
   dist\WIN_CoDroneVisionController.exe --flight-log
   ```

Alternatively, you can double-click `WIN_CoDroneVisionController.exe` directly from Windows File Explorer.

---

### Running on Linux (`LINUX_CoDroneVisionController`)

1. Open a terminal in the project root directory.
2. Ensure the binary has execution permissions:
   ```bash
   chmod +x dist/LINUX_CoDroneVisionController
   ```
3. Launch standard flight mode:
   ```bash
   ./dist/LINUX_CoDroneVisionController
   ```
4. Launch simulation / dry-run mode:
   ```bash
   ./dist/LINUX_CoDroneVisionController --mock-drone --mock-camera
   ```
5. Launch with flight logging enabled:
   ```bash
   ./dist/LINUX_CoDroneVisionController --flight-log
   ```

---

## Building From Source

Follow these steps if you want to modify the source code or build the standalone executable yourself using PyInstaller.

### 1. Environment Requirements
- **Python Version**: Python 3.10 is required for MediaPipe 0.10.21 compatibility.
- **Webcam**: Built-in or external USB camera.
- **Drone Hardware**: Robolink CoDrone Edu quadcopter with USB wireless controller.

### 2. Setup & Virtual Environment Installation

```bash
git clone https://github.com/EmperorRaccoonthe1st/CoDrone-EDU-Hand-Control.git
cd CoDrone-EDU-Hand-Control

# Create virtual environment
python3.10 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install required dependencies
pip install -r requirements.txt
pip install pyinstaller
```

> [!IMPORTANT]
> `mediapipe` version must be strictly `0.10.21` for hand landmark coordinate compatibility.

---

### 3. Run Directly From Source

- **Standard Flight Mode**:
  ```bash
  python main.py
  ```
- **Flight Mode with Telemetry Logging**:
  ```bash
  python main.py --flight-log
  ```
- **Dry-Run Simulation Mode**:
  ```bash
  python main.py --mock-drone --mock-camera
  ```

---

### 4. Build Standalone Executable with PyInstaller

To compile a self-contained portable executable using the provided `main.spec` file:

```bash
pyinstaller --clean main.spec
```

The output executable will be generated inside the `dist/` directory.

---

## Gesture Control Reference

| Gesture Posture | Hand | Action |
| :--- | :--- | :--- |
| **Point Up** | Right Hand | Launch Takeoff & Calibrate Baselines |
| **Thumbs-Up Joystick** | Right Hand | 3D Tilt for Roll, Pitch, and Yaw |
| **Hand Height** | Left Hand | Raise = Ascend (+Throttle) \| Lower = Descend (-Throttle) |
| **1 - 4 Fingers** | Left Hand | Speed Presets (`SPEED_1` 25% ... `SPEED_4` 100%) |
| **Closed Fist** | Left Hand | `HOVER` Pause Mode (Hold Position) |
| **Thumb Down** | Left Hand | `LAND` Safe Landing Sequence |
| **Crossed Wrists** | Both Hands | **EMERGENCY STOP** (Instant Motor Shutdown) |

---

## Running Unit Tests

Run the complete test suite to verify system integrity:
```bash
python -m unittest discover tests
```

---

## License

Distributed under the MIT License. See `LICENSE` for details.
