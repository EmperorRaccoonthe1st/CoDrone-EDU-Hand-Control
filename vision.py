import cv2
import mediapipe as mp
import sys
import time

from state import SystemState, DroneState
from gestures import is_thumbs_up, is_pointing, is_crossed_wrists, classify_left_hand, LeftHandSignal
from telemetry import TelemetryMapper
from flight_logger import FlightLogger


def initialize_camera(max_indices=4):
    if sys.platform.startswith('win'):
        backend = cv2.CAP_DSHOW
        backend_name = "DirectShow"
    elif sys.platform.startswith('linux'):
        backend = cv2.CAP_V4L2
        backend_name = "V4L2"
    else:
        backend = cv2.CAP_ANY
        backend_name = "Default"

    print(f"[*] OS detected: {sys.platform}. Enforcing {backend_name} backend.")

    for index in range(max_indices):
        print(f"[*] Testing camera index {index}...")
        cap = cv2.VideoCapture(index, backend)
        if not cap.isOpened():
            cap.release()
            continue
        
        time.sleep(0.5)
        success, frame = cap.read()
        if success and frame is not None:
            print(f"[+] Success! Active camera locked on index {index}.\n")
            return cap
        else:
            cap.release()

    print("\n[ERROR] FATAL FAULT: Could not initialize any camera.")
    sys.exit(1)


def vision_loop(mock_camera=False, enable_flight_log=False):
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    
    drone_state = DroneState()
    drone_state.set_state(SystemState.SEARCHING)

    logger = FlightLogger(enabled=enable_flight_log)

    if not mock_camera:
        cap = initialize_camera(max_indices=4)
        if cap is None:
            return
        cv2.namedWindow('Drone Controller Vision', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Drone Controller Vision', 1280, 720)

    crossed_frames = 0
    CROSSED_THRESHOLD = 10 
    frame_idx = 0
    takeoff_timestamp = 0.0
    TAKEOFF_DELAY_SEC = 2.0
    neutral_params = {
        'roll_dx': -0.042,
        'pitch_dz': +0.087,
        'yaw_dx': +0.032,
        'left_throttle_y': 0.60,
    }
    neutral_left_norm = None
    neutral_right_norm = None

    print("[*] Loading MediaPipe ML Models into memory...")
    
    with mp_hands.Hands(
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7,
        max_num_hands=2) as hands:
        
        print("[+] MediaPipe loaded. Starting video feed processing.")
        
        while not mock_camera and cap.isOpened():
            success, image = cap.read()
            if not success:
                continue

            image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
            results = hands.process(image)
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            current_state = drone_state.get_state()
            wrists = {"Right": None, "Left": None}
            right_hand_landmarks = None
            left_hand_landmarks = None
            left_signal = LeftHandSignal.HOVER

            if results.multi_hand_landmarks and results.multi_handedness:
                for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                    mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    actual_label = results.multi_handedness[idx].classification[0].label
                    wrist_node = hand_landmarks.landmark[0]
                    wrists[actual_label] = wrist_node

                    h, w, _ = image.shape
                    pixel_x = int(wrist_node.x * w)
                    pixel_y = int(wrist_node.y * h)

                    if actual_label == "Right":
                        right_hand_landmarks = hand_landmarks
                        right_is_pointing = is_pointing(right_hand_landmarks)
                        right_is_joystick = is_thumbs_up(right_hand_landmarks)
                        if right_is_pointing:
                            label_str = "Right (Point Up Launch)"
                        elif right_is_joystick:
                            label_str = "Right (Joystick Active)"
                        else:
                            label_str = "Right (Hand)"

                        cv2.putText(image, label_str, (pixel_x - 40, pixel_y - 20), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)
                    elif actual_label == "Left":
                        left_hand_landmarks = hand_landmarks
                        left_signal = classify_left_hand(left_hand_landmarks)
                        cv2.putText(image, f"Left ({left_signal.name})", (pixel_x - 40, pixel_y - 20), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2, cv2.LINE_AA)

                # 1. Debounced Cross-Hands Killswitch
                if is_crossed_wrists(wrists["Left"], wrists["Right"]):
                    crossed_frames += 1
                    if crossed_frames >= CROSSED_THRESHOLD:
                        drone_state.set_state(SystemState.EMERGENCY_STOP)
                else:
                    crossed_frames = 0

                # 2. Left Hand Safe Landing Trigger
                if left_signal == LeftHandSignal.LAND and current_state == SystemState.MANUAL_CONTROL:
                    print("[*] Left Hand Safe Landing Signal Triggered!")
                    drone_state.set_state(SystemState.SEARCHING)

                # 3. Takeoff Unlock via Right Hand Point Up Gesture (blocked if left hand is signaling LAND)
                if right_hand_landmarks and drone_state.get_state() == SystemState.SEARCHING and left_signal != LeftHandSignal.LAND:
                    if is_pointing(right_hand_landmarks):
                        r_lms = right_hand_landmarks.landmark
                        left_y = left_hand_landmarks.landmark[0].y if left_hand_landmarks else 0.60
                        neutral_params = {
                            'roll_dx': r_lms[4].x - r_lms[0].x,
                            'pitch_dz': r_lms[0].z - r_lms[9].z,
                            'yaw_dx': r_lms[9].x - r_lms[0].x,
                            'left_throttle_y': left_y,
                        }
                        neutral_right_norm = (r_lms[0].x, r_lms[0].y)
                        if left_hand_landmarks:
                            neutral_left_norm = (left_hand_landmarks.landmark[0].x, left_hand_landmarks.landmark[0].y)
                        else:
                            neutral_left_norm = None

                        print(f"[+] Point Up Launch gesture detected! Calibrated dual-hand baseline and initiating takeoff...")
                        drone_state.set_state(SystemState.MANUAL_CONTROL)
                        takeoff_timestamp = time.time()

                # Auto-calibrate left hand neutral baseline if left hand appears after takeoff
                if drone_state.get_state() == SystemState.MANUAL_CONTROL and left_hand_landmarks and neutral_left_norm is None:
                    neutral_left_norm = (left_hand_landmarks.landmark[0].x, left_hand_landmarks.landmark[0].y)
                    neutral_params['left_throttle_y'] = left_hand_landmarks.landmark[0].y

                # 4. Telemetry Calculation during Manual Control
                if drone_state.get_state() == SystemState.MANUAL_CONTROL:
                    time_since_takeoff = time.time() - takeoff_timestamp
                    if time_since_takeoff < TAKEOFF_DELAY_SEC:
                        # 2-second post-launch warmup delay: zero telemetry
                        drone_state.update_flight_commands(0, 0, 0, 0)
                    else:
                        roll, pitch, yaw, throttle = TelemetryMapper.process_dual_hand_telemetry(
                            right_hand_landmarks, left_hand_landmarks, left_signal, neutral_params=neutral_params
                        )
                        drone_state.update_flight_commands(roll, pitch, yaw, throttle)
                else:
                    drone_state.update_flight_commands(0, 0, 0, 0)

            current_state = drone_state.get_state()
            roll, pitch, yaw, throttle = drone_state.get_flight_commands()

            # Render Neutral Baseline Target Dots on HUD
            if current_state == SystemState.MANUAL_CONTROL:
                h, w, _ = image.shape
                # Left Hand Height Neutral Target Dot
                if neutral_left_norm:
                    lx = int(neutral_left_norm[0] * w)
                    ly = int(neutral_left_norm[1] * h)
                    cv2.circle(image, (lx, ly), 12, (255, 255, 0), 2, cv2.LINE_AA)
                    cv2.circle(image, (lx, ly), 4, (255, 255, 0), -1, cv2.LINE_AA)
                    text_lx = max(10, min(w - 230, lx + 15))
                    cv2.putText(image, "LEFT HEIGHT NEUTRAL", (text_lx, ly + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2, cv2.LINE_AA)
                    if left_hand_landmarks:
                        curr_lx = int(left_hand_landmarks.landmark[0].x * w)
                        curr_ly = int(left_hand_landmarks.landmark[0].y * h)
                        cv2.line(image, (lx, ly), (curr_lx, curr_ly), (0, 255, 255), 2, cv2.LINE_AA)

                # Right Hand Joystick Neutral Target Dot
                if neutral_right_norm:
                    rx = int(neutral_right_norm[0] * w)
                    ry = int(neutral_right_norm[1] * h)
                    cv2.circle(image, (rx, ry), 12, (0, 255, 0), 2, cv2.LINE_AA)
                    cv2.circle(image, (rx, ry), 4, (0, 255, 0), -1, cv2.LINE_AA)
                    text_rx = max(10, min(w - 250, rx + 15))
                    cv2.putText(image, "RIGHT JOYSTICK NEUTRAL", (text_rx, ry + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2, cv2.LINE_AA)
                    if right_hand_landmarks:
                        curr_rx = int(right_hand_landmarks.landmark[0].x * w)
                        curr_ry = int(right_hand_landmarks.landmark[0].y * h)
                        cv2.line(image, (rx, ry), (curr_rx, curr_ry), (0, 255, 0), 2, cv2.LINE_AA)

            # Dynamic HUD overlay (Full Cyberpunk Sci-Fi Design)
            w = image.shape[1]
            h = image.shape[0]

            # 1. Viewfinder Corner Reticles (Sci-Fi Brackets)
            cl = 22  # Bracket corner length
            co = 55  # Offset below top bar / above bottom bar
            mode_color = (0, 255, 0) if current_state == SystemState.MANUAL_CONTROL else ((0, 255, 255) if current_state == SystemState.SEARCHING else (0, 0, 255))

            # Top-Left Bracket
            cv2.line(image, (15, co), (15 + cl, co), mode_color, 2, cv2.LINE_AA)
            cv2.line(image, (15, co), (15, co + cl), mode_color, 2, cv2.LINE_AA)
            # Top-Right Bracket
            cv2.line(image, (w - 15, co), (w - 15 - cl, co), mode_color, 2, cv2.LINE_AA)
            cv2.line(image, (w - 15, co), (w - 15, co + cl), mode_color, 2, cv2.LINE_AA)
            # Bottom-Left Bracket
            cv2.line(image, (15, h - co), (15 + cl, h - co), mode_color, 2, cv2.LINE_AA)
            cv2.line(image, (15, h - co), (15, h - co - cl), mode_color, 2, cv2.LINE_AA)
            # Bottom-Right Bracket
            cv2.line(image, (w - 15, h - co), (w - 15 - cl, h - co), mode_color, 2, cv2.LINE_AA)
            cv2.line(image, (w - 15, h - co), (w - 15, h - co - cl), mode_color, 2, cv2.LINE_AA)

            # 2. Top & Bottom HUD Bars with Neon Accent Edges
            cv2.rectangle(image, (0, 0), (w, 45), (10, 12, 15), -1)
            cv2.rectangle(image, (0, h - 42), (w, h), (10, 12, 15), -1)
            cv2.line(image, (0, 45), (w, 45), mode_color, 2, cv2.LINE_AA)
            cv2.line(image, (0, h - 42), (w, h - 42), (0, 255, 255), 2, cv2.LINE_AA)

            # 3. Dynamic Pill Badges for System State & Speed
            if current_state == SystemState.MANUAL_CONTROL:
                time_since_takeoff = time.time() - takeoff_timestamp
                if time_since_takeoff < TAKEOFF_DELAY_SEC:
                    rem_sec = TAKEOFF_DELAY_SEC - time_since_takeoff
                    end_x = 290 if w >= 900 else 220
                    cv2.rectangle(image, (15, 8), (end_x, 36), (35, 35, 15), -1)
                    cv2.rectangle(image, (15, 8), (end_x, 36), (0, 255, 255), 1, cv2.LINE_AA)
                    cv2.putText(image, f"TAKEOFF WARMUP ({rem_sec:.1f}s)", (23, 27), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2, cv2.LINE_AA)
                else:
                    # Mode Badge
                    cv2.rectangle(image, (15, 8), (105, 36), (20, 45, 20), -1)
                    cv2.rectangle(image, (15, 8), (105, 36), (0, 255, 0), 1, cv2.LINE_AA)
                    cv2.putText(image, "MANUAL", (25, 27), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2, cv2.LINE_AA)
                    # Speed Badge
                    spd_name = left_signal.name
                    cv2.rectangle(image, (115, 8), (225, 36), (35, 35, 15), -1)
                    cv2.rectangle(image, (115, 8), (225, 36), (0, 255, 255), 1, cv2.LINE_AA)
                    cv2.putText(image, spd_name, (125, 27), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2, cv2.LINE_AA)
            elif current_state == SystemState.SEARCHING:
                end_x = 320 if w >= 900 else 240
                cv2.rectangle(image, (15, 8), (end_x, 36), (35, 35, 15), -1)
                cv2.rectangle(image, (15, 8), (end_x, 36), (0, 255, 255), 1, cv2.LINE_AA)
                cv2.putText(image, "SEARCHING (POINT UP TO LAUNCH)" if w >= 900 else "SEARCHING (POINT UP)", (23, 27), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2, cv2.LINE_AA)
            else:
                end_x = 320 if w >= 900 else 180
                cv2.rectangle(image, (15, 8), (end_x, 36), (45, 15, 15), -1)
                cv2.rectangle(image, (15, 8), (end_x, 36), (0, 0, 255), 1, cv2.LINE_AA)
                cv2.putText(image, "EMERGENCY STOP (ARMS CROSSED)" if w >= 900 else "EMERGENCY STOP", (23, 27), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2, cv2.LINE_AA)

            # 4. Battery Icon Gauge
            sensor_data = drone_state.get_sensor_data()
            bat_pct = int(sensor_data.get("battery", 100))
            bat_color = (0, 255, 0) if bat_pct >= 30 else ((0, 255, 255) if bat_pct >= 15 else (0, 0, 255))
            bat_x = w - (230 if enable_flight_log else 115)

            # Outer battery shell + terminal nipple
            cv2.rectangle(image, (bat_x, 14), (bat_x + 28, 32), bat_color, 2, cv2.LINE_AA)
            cv2.rectangle(image, (bat_x + 28, 19), (bat_x + 30, 27), bat_color, -1)
            # Inner fill bar
            fill_w = int((bat_pct / 100.0) * 22)
            if fill_w > 0:
                cv2.rectangle(image, (bat_x + 3, 17), (bat_x + 3 + fill_w, 29), bat_color, -1)
            # Percentage text
            cv2.putText(image, f"{bat_pct}%", (bat_x + 36, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.5, bat_color, 2, cv2.LINE_AA)

            # 5. REC Logging Badge
            if enable_flight_log:
                rec_x = w - 75
                cv2.circle(image, (rec_x - 12, 22), 5, (0, 0, 255), -1, cv2.LINE_AA)
                cv2.putText(image, "REC", (rec_x, 27), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2, cv2.LINE_AA)

            # 6. Bottom Bar Telemetry with Analog Level Mini-Gauges
            if current_state in (SystemState.SEARCHING, SystemState.EMERGENCY_STOP):
                disp_roll, disp_pitch, disp_yaw, disp_throttle = 0, 0, 0, 0
            else:
                disp_roll, disp_pitch, disp_yaw, disp_throttle = roll, pitch, yaw, throttle

            if w >= 900:
                cmd_text = f"ROLL:{disp_roll:+4d} | PITCH:{disp_pitch:+4d} | YAW:{disp_yaw:+4d} | THROTTLE:{disp_throttle:+4d}"
            else:
                cmd_text = f"R:{disp_roll:+3d}  P:{disp_pitch:+3d}  Y:{disp_yaw:+3d}  T:{disp_throttle:+3d}"

            cv2.putText(image, cmd_text, (15, h - 14), cv2.FONT_HERSHEY_SIMPLEX, 0.58 if w < 900 else 0.65, (0, 255, 255), 2, cv2.LINE_AA)

            # Analog Level Mini-Gauges for Pitch & Roll (Right Side of Bottom Bar)
            if w >= 600:
                gx = w - 155
                # Pitch Level Bar
                cv2.putText(image, "P", (gx - 18, h - 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1, cv2.LINE_AA)
                cv2.rectangle(image, (gx, h - 26), (gx + 60, h - 14), (50, 50, 50), 1)
                p_bar = int((disp_pitch / 100.0) * 30)
                cp = gx + 30
                cv2.line(image, (cp, h - 26), (cp, h - 14), (180, 180, 180), 1)
                if p_bar != 0:
                    cv2.rectangle(image, (cp, h - 25), (cp + p_bar, h - 15), (0, 255, 255), -1)

                # Roll Level Bar
                cv2.putText(image, "R", (gx + 72, h - 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1, cv2.LINE_AA)
                cv2.rectangle(image, (gx + 85, h - 26), (gx + 145, h - 14), (50, 50, 50), 1)
                r_bar = int((disp_roll / 100.0) * 30)
                cr = gx + 115
                cv2.line(image, (cr, h - 26), (cr, h - 14), (180, 180, 180), 1)
                if r_bar != 0:
                    cv2.rectangle(image, (cr, h - 25), (cr + r_bar, h - 15), (0, 255, 255), -1)

            # Record telemetry frame log & snapshot if monitoring mode is active
            frame_idx += 1
            logger.log_frame(
                frame_idx=frame_idx,
                system_state=current_state.name,
                left_signal=left_signal,
                left_hand_landmarks=left_hand_landmarks,
                right_hand_landmarks=right_hand_landmarks,
                flight_commands=(roll, pitch, yaw, throttle),
                sensor_data=sensor_data,
                neutral_params=neutral_params,
                image_frame=image
            )

            if not mock_camera:
                cv2.imshow('Drone Controller Vision', image)
                key = cv2.waitKey(5) & 0xFF
                if key == ord('q'):
                    drone_state.set_state(SystemState.EMERGENCY_STOP)
                    break
                elif key == ord('r'):
                    drone_state.set_state(SystemState.SEARCHING)
                    crossed_frames = 0

    if not mock_camera:
        cap.release()
        cv2.destroyAllWindows()

    logger.close()


if __name__ == "__main__":
    vision_loop()