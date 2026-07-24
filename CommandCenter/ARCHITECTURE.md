# System Architecture: CoDrone Edu Vision Controller

## 1. Overview & Core Philosophy

The CoDrone Edu Vision Controller is a real-time, low-latency flight controller system that translates computer vision tracking (body posture and dual-hand gestures) into flight telemetry for a CoDrone Edu.

To guarantee flight safety, responsive control, and high frame rates, the system adopts a decoupled, multi-threaded architecture anchored by a thread-safe Singleton state machine and a strict dual-hand control delegation model.

---

## 2. Dual-Hand Control Division

```
               [ Dual-Hand MediaPipe Vision Tracking ]
                                  │
         ┌────────────────────────┴────────────────────────┐
         ▼                                                 ▼
[ LEFT HAND: Speed & Land ]                 [ RIGHT HAND: 3D Virtual Joystick ]
 - Closed Fist: Hover (0%)                   - Thumbs Up: Activate Joystick / Takeoff
 - 1 Finger Up: Speed 1 (25%)                - Screen Height: Elevation / Throttle
 - 2 Fingers Up: Speed 2 (50%)               - 3D Tilt Forward/Back: Pitch
 - 3 Fingers Up: Speed 3 (75%)               - 3D Sideways Tilt: Roll
 - 4 Fingers Up: Speed 4 (100%)              - Hand Turn Angle: Yaw
 - Thumb Down: Safe Land Signal
```

---

## 3. High-Level System Architecture

```mermaid
graph TD
    subgraph Vision Processing Thread [Main / GUI Thread]
        Cam[Camera Ingestion & OS Backend] --> Flip[Image Preprocessing & Flip]
        Flip --> MP[MediaPipe Hands 0.10.21]
        MP --> LeftGest[Left Hand Speed Classifier]
        MP --> RightGest[Right Hand Thumbs Up Joystick Mapper]
        LeftGest --> Map[Dual-Hand Telemetry Normalizer]
        RightGest --> Map
        Map --> HUD[OpenCV Visual HUD Overlay]
    end

    subgraph Shared Memory Barrier [Thread-Safe Singleton]
        State[DroneState Shared Memory]
        Lock[(threading.Lock)]
        State --- Lock
    end

    subgraph Drone Hardware Worker Thread [Background Thread]
        SDK[CoDrone Edu SDK Driver]
        Loop[Fixed-Tick Control Loop (20 Hz)]
        SDK --- Loop
    end

    LeftGest -- Safe Landing Signal --> State
    RightGest -- Thumbs Up Unlock --> State
    Map -- Telemetry Vectors (Roll, Pitch, Yaw, Throttle) --> State
    State -- Thread-Safe Polling --> Loop
    Loop -- Bluetooth Serial Commands --> PhysicalDrone[CoDrone Edu Hardware]
```
