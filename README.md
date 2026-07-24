# 🛸 CoDrone Edu Vision Controller

An ML-powered computer vision gesture flight controller for the **Robolink CoDrone Edu**, featuring **MediaPipe 3D Hand Landmark Tracking**, a **Virtual 3D Joystick**, and **Real-Time Telemetry Logging**.

![Visual HUD Overlay](https://img.shields.io/badge/UI-Professional_HUD_Overlay-blue?style=for-the-badge)
![MediaPipe](https://img.shields.io/badge/AI-MediaPipe_0.10.21-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.9+-yellow?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

---

## ✨ Features

- **🎮 Dual-Hand Gesture Flight Control**:
  - **Right Hand Point Up**: Launch takeoff & calibrate neutral flight baselines.
  - **Right Hand Thumbs-Up Joystick**: 3D orientation tilt for Roll, Pitch, and Yaw translation.
  - **Left Hand Altitude Throttle**: Screen height controls vertical climb & descent.
  - **Left Hand Speed Presets**: Extend 1 to 4 fingers to select translation speed multipliers ($25\%, 50\%, 75\%, 100\%$).
  - **Left Hand Hover Pause**: Closed fist pauses translation for safe pilot re-orientation.
  - **Left Hand Safe Landing**: Thumb-Down fist lands the drone safely.
  - **Crossed Wrists Deadman Killswitch**: Crossing wrists in an "X" posture engages instant hardware motor shutdown.
- **🌌 Professional Visual HUD Overlay**:
  - Glassmorphic top & bottom status bars with neon accent borders.
  - Viewfinder corner reticles and dynamic mode pill badges.
  - Battery Icon Gauge with inner fill level bar and low-voltage color alerts.
  - Analog Pitch and Roll mini level bars on bottom bar.
  - Resolution-adaptive text formatting (adapts cleanly to 640p, 720p, and 1080p windows).
- **📊 Session Flight Monitoring & Frame Saver**:
  - Automatically records timestamped telemetry CSV logs and JPEG snapshot frames under `logs/session_YYYYMMDD_HHMMSS/`.

---

## 🛠️ Hardware Requirements

1. **Robolink CoDrone Edu** quadcopter.
2. **CoDrone Edu USB Wireless Bluetooth Dongle** (connected to host machine).
3. **Webcam** (USB webcam or laptop built-in camera).
4. **Windows / macOS / Linux PC** running Python 3.9+.

---

## 🚀 Quick Start Guide

### Option 1: 1-Click Portable Windows Installer (USB Friendly)
Simply double-click **`Installer.bat`** from Windows Explorer or your USB drive!
- Automatically detects/installs Python if missing on a fresh Windows PC.
- Sets up local isolated virtual environment (`.venv`).
- Installs all dependencies (`mediapipe 0.10.21`, `opencv-python`, `codrone-edu`).
- Launches the application or compiles a standalone `.exe`.

---

### Option 2: Command Line Setup

```bash
git clone https://github.com/EmperorRaccoonthe1st/CoDrone-EDU-Hand-Control.git
cd CoDrone-EDU-Hand-Control

# Install required dependencies
pip install -r requirements.txt
```

> [!IMPORTANT]
> `mediapipe` version must be strictly `0.10.21` for hand landmark coordinate compatibility.

---

### 2. Run the Controller

#### Standard Flight Mode (Real Drone + Real Camera):
```bash
python main.py
```

#### Flight Mode with Telemetry & Frame Logging (`--flight-log`):
```bash
python main.py --flight-log
```

#### Dry-Run Simulation Mode (No Drone or Camera required):
```bash
python main.py --mock-drone --mock-camera
```

---

## 🎮 Gesture Control Reference

| Gesture Posture | Hand | Action |
| :--- | :--- | :--- |
| ☝️ **Point Up** | Right Hand | Launch Takeoff & Calibrate Baselines |
| 👍 **Thumbs-Up Joystick** | Right Hand | 3D Tilt for Roll, Pitch, and Yaw |
| ↕️ **Hand Height** | Left Hand | Raise = Ascend (+Throttle) \| Lower = Descend (-Throttle) |
| 🖐️ **1 - 4 Fingers** | Left Hand | Speed Presets (`SPEED_1` 25% $\dots$ `SPEED_4` 100%) |
| ✊ **Closed Fist** | Left Hand | `HOVER` Pause Mode (Hold Position) |
| 👎 **Thumb Down** | Left Hand | `LAND` Safe Landing Sequence |
| 🙅 **Crossed Wrists** | Both Hands | **EMERGENCY STOP** (Instant Motor Shutdown) |

---

## 🧪 Running Unit Tests

Run the complete test suite to verify system integrity:
```bash
python -m unittest discover tests
```

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for details.
