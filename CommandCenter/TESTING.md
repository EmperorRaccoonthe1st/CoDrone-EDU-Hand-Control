# Quality Assurance & Testing Protocol (TESTING.md)

> **Mandatory Rule:** Comprehensive empirical verification is required after **EVERY** code modification to ensure system stability, lock safety, and flight controller accuracy.

---

## 1. Multi-Tiered Testing Strategy

To prevent hardware crashes and runtime bugs, testing is divided into 4 mandatory tiers:

```
[ Tier 1: Unit & Lock Safety Tests ] -> [ Tier 2: Synthetic Vision & Gesture Tests ] -> [ Tier 3: Dry-Run / Mock Hardware Test ] -> [ Tier 4: Physical Flight Test ]
```

---

## 2. Tier 1: Unit & Thread Safety Testing

### 2.1. `DroneState` Concurrent Access Verification
* **Objective:** Ensure no race conditions or deadlocks occur when reading/writing shared memory between Vision and Hardware threads.
* **Test Procedure:**
  1. Spawn 10 concurrent reader threads calling `get_state()` and `get_flight_commands()`.
  2. Spawn 10 concurrent writer threads calling `update_flight_commands()` and `set_state()`.
  3. Execute 100,000 iterations and assert no exceptions or unhandled lock states occur.

### 2.2. Telemetry Clamping Test
* **Objective:** Verify telemetry parameters strictly remain bounded in `[-100, 100]`.
* **Inputs:** Test extreme inputs (e.g. `roll = 9999`, `pitch = -500`).
* **Expected Output:** `get_flight_commands()` returns `(100, -100, ...)`.

---

## 3. Tier 2: Synthetic Gesture Engine Testing

### 3.1. `is_pointing()` Landmark Test Matrix
* **Objective:** Verify pointing gesture classifier accuracy using mock MediaPipe landmark objects.

| Case | Index Tip (8) vs PIP (6) | Middle Tip (12) vs PIP (10) | Ring Tip (16) vs PIP (14) | Pinky Tip (20) vs PIP (18) | Wrist (0) vs Index (8) | Expected Result |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **Valid Point** | `y(8) < y(6)` | `y(12) > y(10)` | `y(16) > y(14)` | `y(20) > y(18)` | `y(0) - y(8) > 0.25` | `True` |
| **Open Palm** | `y(8) < y(6)` | `y(12) < y(10)` | `y(16) < y(14)` | `y(20) < y(18)` | `y(0) - y(8) > 0.25` | `False` |
| **Fist** | `y(8) > y(6)` | `y(12) > y(10)` | `y(16) > y(14)` | `y(20) > y(18)` | `y(0) - y(8) < 0.25` | `False` |
| **Hand Too Low**| `y(8) < y(6)` | `y(12) > y(10)` | `y(16) > y(14)` | `y(20) > y(18)` | `y(0) - y(8) = 0.10` | `False` |

---

## 4. Tier 3: Dry-Run / Mock Hardware Test (HIL Simulation)

Before flying real hardware, run the system in `--mock-drone` mode.

### 4.1. Vision & Keyboard Control Verification Protocol
Run the main script with `--mock-drone`:
1. **Camera Initialization Check:** Verify logs confirm camera backend detection (`DirectShow` on Windows / `V4L2` on Linux) and non-hanging frame capture.
2. **Initial State Check:** Verify HUD displays `STATE: SEARCHING` in Cyan.
3. **Point Gesture Takeoff Test:** Perform pointing gesture into camera.
   * *Pass Criteria:* HUD transitions to `STATE: MANUAL CONTROL (FLYING)` in Green within 500ms.
4. **Crossed-Arms Emergency Stop Test:** Cross arms in front of camera.
   * *Pass Criteria:* HUD debounces 10 frames and locks into `STATE: EMERGENCY STOP` in Red.
5. **Keyboard Reset Test:** Press `r`.
   * *Pass Criteria:* System state resets back to `SEARCHING`.
6. **Keyboard Emergency Kill Test:** Press `q`.
   * *Pass Criteria:* System triggers `EMERGENCY_STOP` and exits vision loop cleanly without crashing.

---

## 5. Tier 4: Live Flight Physical Verification Protocol

> ⚠️ **Safety Pre-Check:** Ensure drone battery > 50%, prop guards are installed, flight path is cleared of obstacles, and safety goggles are worn.

### 5.1. Live Flight Test Sequence
1. Place CoDrone Edu on flat surface.
2. Launch controller script: `python main.py`.
3. Verify Bluetooth pairing log: `[+] CoDrone Edu successfully paired!`.
4. Perform Pointing Gesture to trigger `Takeoff`. Verify drone hovers stably at ~1m.
5. Move right hand slightly Left/Right/Up/Down to verify Roll and Pitch responses.
6. Perform Crossed-Arms gesture. Verify drone cuts motors/lands immediately within **< 300ms**.
7. Press `q` to terminate flight session safely.

---

## 6. Post-Edit Regression Checklist

After modifying **ANY** file:
- [ ] Run `python -m unittest discover tests` (all unit tests must pass).
- [ ] Run `python main.py --mock-drone` to verify camera feed, HUD, and keyboard hotkeys.
- [ ] Confirm no deprecation warnings from MediaPipe or OpenCV.
- [ ] Inspect console output for uncaught background thread exceptions.
