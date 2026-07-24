# Technical Specification (SPEC.md): CoDrone Edu Vision Controller

> **Source of Truth:** This document defines the exact specs, data contracts, mathematical formulas, and operational bounds for the entire codebase.

---

## 1. System Specifications & Dependencies

### 1.1. Environment
* **Python Runtime:** `Python >= 3.12` (isolated in `.venv`).
* **MediaPipe Version:** `mediapipe==0.10.21` (**STRICT DEPIN LOCK**). Do not upgrade beyond `0.10.30`.
* **OpenCV Version:** `opencv-python>=4.8.0`.
* **Drone SDK:** `codrone_edu`.

### 1.2. OS-Specific Camera Backends
* **Windows (`sys.platform.startswith('win')`):** Enforces `cv2.CAP_DSHOW` (DirectShow).
* **Linux (`sys.platform.startswith('linux')`):** Enforces `cv2.CAP_V4L2` (Video4Linux2).
* **Camera Warmup:** Sleep `0.5s` after `cap.isOpened()`.

---

## 2. Dual-Hand Control Architecture

The control system delegates responsibilities strictly across both hands:
* **Left Hand:** Master Speed Presets (Hover, Speed 1-4) & Safe Landing command.
* **Right Hand:** 3D Virtual Joystick (Thumbs Up gesture & 3D hand orientation/elevation).

---

## 3. Left Hand Gesture Specifications (Speed & Landing)

Rotation-invariant 3D Euclidean distance ratio: $\text{Ratio} = \frac{\text{Distance}(\text{Wrist}, \text{Tip})}{\text{Distance}(\text{Wrist}, \text{PIP})}$. Finger extended if $\text{Ratio} > 1.22$, folded if $\text{Ratio} \le 1.22$.

| Finger Count / Gesture | Landmark Condition | Mode / Speed Preset | Speed Multiplier |
| :--- | :--- | :--- | :---: |
| **0 Fingers (Closed Fist)** | All 4 finger tips folded ($\text{Ratio} \le 1.22$) | **Hover / Neutral** | `0%` |
| **1 Finger (Index Only)** | Index extended ($\text{Ratio} > 1.22$); others folded | **Speed 1** | `25%` |
| **2 Fingers (Index + Middle)** | Index, Middle extended; Ring, Pinky folded | **Speed 2** | `50%` |
| **3 Fingers (Index + Middle + Ring)** | Index, Middle, Ring extended; Pinky folded | **Speed 3** | `75%` |
| **4 Fingers (All 4 Fingers Up)** | Index, Middle, Ring, Pinky extended | **Speed 4** | `100%` |
| **Thumb Down (Fist + Thumb Down)** | Thumb Tip below MCP/Wrist (`y(4) > y(2)`), **AND ALL 4 NON-THUMB FINGERS FOLDED** | **Safe Landing** | State -> `SEARCHING` / Land |

---

## 4. Right Hand Virtual Joystick & Launch Specifications

### 4.1. Left Hand Control Scheme (Speed Presets, Landing, & Height Control)
* **Speed 0 (Hover):** Closed Fist $\rightarrow$ 0% translation speed.
* **Speed 1 (25%):** 1 Finger Extended (Index) $\rightarrow$ 25% max translation speed.
* **Speed 2 (50%):** 2 Fingers Extended (Index + Middle) $\rightarrow$ 50% max translation speed.
* **Speed 3 (75%):** 3 Fingers Extended (Index + Middle + Ring) $\rightarrow$ 75% max translation speed.
* **Speed 4 (100%):** 4 Fingers Extended (Index + Middle + Ring + Pinky) $\rightarrow$ 100% max translation speed.
* **Safe Landing Signal:** Thumb Down with 4 non-thumb fingers folded into a fist
* **Professional Visual HUD Overlay:**
  * **Top & Bottom HUD Bars:** Glassmorphic dark bars with neon green/cyan accent border lines.
  * **Viewfinder Corner Reticles:** 4-corner L-shaped camera viewfinder brackets matching state color.
  * **Dynamic Pill Badges:** System state (`MANUAL`) and speed presets (`SPEED_1`..`SPEED_4`) rendered in dark filled pill badges with thin neon borders.
  * **Battery Icon Gauge:** Real-time battery indicator featuring an outer battery shell icon, inner filled charge level bar, and percentage text (`[■■■] 85%`) with dynamic color shifts (Green $\ge 30\%$, Yellow $15-29\%$, Red $<15\%$).
  * **Mini Analog Telemetry Level Bars:** Real-time horizontal pitch tilt and roll bank level gauges on the right side of the bottom telemetry bar.
* **Height / Elevation / Throttle:** Left Hand screen height relative to left hand neutral launch height (`neutral_left_throttle_y`).
  * Left Wrist raised above neutral $\rightarrow$ Ascend (+ throttle).
  * Left Wrist lowered below neutral $\rightarrow$ Descend (- throttle).
  * Left Wrist at neutral $\rightarrow$ Stable Hover (0 throttle).

### 4.2. Right Hand Virtual 3D Joystick (Pitch & Roll Controls)
* **Launch Trigger:** Point Up gesture (`is_pointing`) triggers takeoff and calibrates dual-hand neutral baselines.
* **Pitch (Whole-Hand Forward / Backward Tilt):** Derived from 3D Z-depth offset between Wrist (0) and Middle MCP (9) relative to launch baseline.
* **Roll (Whole-Hand Left / Right Bank):** Derived from Thumb Tip (4) X-offset relative to Wrist (0) compared to launch baseline.
* **Yaw:** Temporarily disabled (0) for pitch & roll fine-tuning.

### 4.3. Visual HUD Baseline Neutral Markers
* **Left Height Neutral Target Dot (Cyan):** A target dot (`LEFT HEIGHT NEUTRAL`) renders at the left hand's launch location with a dynamic line extending to current left wrist position.
* **Right Joystick Neutral Target Dot (Green):** A target dot (`RIGHT JOYSTICK NEUTRAL`) renders at the right hand's launch location with a dynamic line extending to current right wrist position.

---

## 5. State Machine Integration (`DroneState`)

```python
class SystemState(Enum):
    INIT = 0
    SEARCHING = 1
    MANUAL_CONTROL = 2
    EMERGENCY_STOP = 3
```

### Emergency Override & Reset
* **Crossed Arms:** 10 consecutive frames locks into `EMERGENCY_STOP`.
* **Keyboard Overrides:** `q` -> `EMERGENCY_STOP`, `r` -> Reset to `SEARCHING`.

---

## 6. Flight Monitoring Logger Mode (`--flight_log` / `--fight_log`)

### 6.1. CLI Invocation
```bash
python main.py --flight_log
```
*(Also supports flag aliases: `--fight_log`, `--flight-log`, `--fight-log`)*

### 6.2. Log Output & Directory
* Automatically creates timestamped CSV log files under the `logs/` directory:
  `logs/flight_log_YYYYMMDD_HHMMSS.csv`

### 6.3. Captured Data Fields
1. **Time & System State:** `timestamp_iso`, `timestamp_unix`, `frame_index`, `system_state`.
2. **User Hand Orientation Metrics:**
   * `left_signal`: Active left-hand gesture (`HOVER`, `SPEED_1`..`SPEED_4`, `LAND`).
   * `left_wrist_y`: Left hand wrist screen height ($Y$).
   * `right_thumb_dx`: Right hand $\Delta X$ (Thumb tip vs. Wrist).
   * `right_pitch_dz`: Right hand 3D Z-depth offset ($\Delta Z$).
   * `right_yaw_dx`: Right hand $\Delta X$ (Knuckles vs. Wrist).
3. **Resultant Flight Inputs:** `command_roll`, `command_pitch`, `command_yaw`, `command_throttle` ($-100$ to $+100$).
4. **Live Sensor Telemetry:**
   * `battery_pct`: Battery percentage ($0 - 100\%$).
   * `height_cm`: ToF height sensor distance in cm.
   * `temp_c`: Board temperature in °C.
   * `pressure_pa`: Barometric pressure in Pa.
   * `accel_x`, `accel_y`, `accel_z`: 3-axis accelerometer readings.
   * `gyro_roll`, `gyro_pitch`, `gyro_yaw`: 3-axis gyro orientation.
   * `pos_x`, `pos_y`: Optical flow position metrics.
