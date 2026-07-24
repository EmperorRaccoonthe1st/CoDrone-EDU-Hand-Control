import os
import csv
import cv2
import threading
from datetime import datetime
from gestures import LeftHandSignal


class FlightLogger:
    """
    Flight Telemetry & Sensor Monitoring Logger for CoDrone Edu.
    Creates a timestamped session subdirectory under logs/ containing:
    - flight_log.csv
    - frames/ (automatic JPEG frame snapshots captured every N frames, specifically targeting Pitch controls)
    """
    HEADER = [
        "timestamp_iso",
        "timestamp_unix",
        "frame_index",
        "saved_frame",
        "system_state",
        "left_signal",
        "left_wrist_y",
        "right_thumb_dx",
        "right_pitch_dz",
        "neutral_pitch_dz",
        "pitch_delta",
        "right_yaw_dx",
        "command_roll",
        "command_pitch",
        "command_yaw",
        "command_throttle",
        "battery_pct",
        "height_cm",
        "temp_c",
        "pressure_pa",
        "accel_x",
        "accel_y",
        "accel_z",
        "gyro_roll",
        "gyro_pitch",
        "gyro_yaw",
        "pos_x",
        "pos_y"
    ]

    def __init__(self, enabled: bool = False, log_dir: str = "logs", save_frame_interval: int = 5):
        self.enabled = enabled
        self.log_dir = log_dir
        self.save_frame_interval = save_frame_interval
        self.session_dir = None
        self.frames_dir = None
        self.filepath = None
        self.file_handle = None
        self.csv_writer = None
        self.lock = threading.Lock()
        self.record_count = 0
        self.saved_frames_count = 0

        if self.enabled:
            self._initialize_session()

    def _initialize_session(self):
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = os.path.join(self.log_dir, f"session_{timestamp_str}")
        self.frames_dir = os.path.join(self.session_dir, "frames")

        os.makedirs(self.frames_dir, exist_ok=True)

        self.filepath = os.path.join(self.session_dir, "flight_log.csv")
        self.file_handle = open(self.filepath, mode="w", newline="", encoding="utf-8")
        self.csv_writer = csv.writer(self.file_handle)
        self.csv_writer.writerow(self.HEADER)
        self.file_handle.flush()

        print(f"[+] Flight Monitoring Logger active!")
        print(f"    - Session Directory : {self.session_dir}")
        print(f"    - Telemetry Log CSV : {self.filepath}")
        print(f"    - Frame Saver Dir   : {self.frames_dir} (saving every {self.save_frame_interval} frames)")

    def log_frame(
        self,
        frame_idx: int,
        system_state: str,
        left_signal: LeftHandSignal,
        left_hand_landmarks,
        right_hand_landmarks,
        flight_commands: tuple[int, int, int, int],
        sensor_data: dict,
        neutral_params: dict = None,
        image_frame = None
    ):
        if not self.enabled or not self.csv_writer:
            return

        with self.lock:
            now = datetime.now()
            iso_ts = now.isoformat()
            unix_ts = round(now.timestamp(), 3)

            # Left Hand Orientation Metrics
            left_wrist_y = ""
            if left_hand_landmarks and hasattr(left_hand_landmarks, "landmark"):
                left_wrist_y = round(left_hand_landmarks.landmark[0].y, 4)

            # Right Hand 3D Orientation Metrics & Targeted Pitch Diagnostics
            right_thumb_dx = ""
            right_pitch_dz = ""
            neutral_pitch_dz = ""
            pitch_delta = ""
            right_yaw_dx = ""

            if neutral_params:
                neutral_pitch_dz = round(neutral_params.get("pitch_dz", 0.087), 4)

            if right_hand_landmarks and hasattr(right_hand_landmarks, "landmark"):
                lms = right_hand_landmarks.landmark
                w0 = lms[0]
                t4 = lms[4]
                m9 = lms[9]
                right_thumb_dx = round(t4.x - w0.x, 4)
                raw_p_dz = w0.z - m9.z
                right_pitch_dz = round(raw_p_dz, 4)
                right_yaw_dx = round(m9.x - w0.x, 4)

                if neutral_pitch_dz != "":
                    pitch_delta = round(raw_p_dz - neutral_pitch_dz, 4)

            # Automatic Frame Saver logic
            saved_frame_relpath = ""
            if image_frame is not None and (frame_idx % self.save_frame_interval == 0 or frame_idx == 1):
                frame_filename = f"frame_{frame_idx:06d}.jpg"
                frame_fullpath = os.path.join(self.frames_dir, frame_filename)
                cv2.imwrite(frame_fullpath, image_frame)
                saved_frame_relpath = os.path.join("frames", frame_filename)
                self.saved_frames_count += 1

            roll_cmd, pitch_cmd, yaw_cmd, throttle_cmd = flight_commands
            sig_name = left_signal.name if isinstance(left_signal, LeftHandSignal) else str(left_signal)

            row = [
                iso_ts,
                unix_ts,
                frame_idx,
                saved_frame_relpath,
                system_state,
                sig_name,
                left_wrist_y,
                right_thumb_dx,
                right_pitch_dz,
                neutral_pitch_dz,
                pitch_delta,
                right_yaw_dx,
                roll_cmd,
                pitch_cmd,
                yaw_cmd,
                throttle_cmd,
                sensor_data.get("battery", 100),
                sensor_data.get("height_cm", 0.0),
                sensor_data.get("temperature_c", 25.0),
                sensor_data.get("pressure_pa", 101325.0),
                sensor_data.get("accel_x", 0.0),
                sensor_data.get("accel_y", 0.0),
                sensor_data.get("accel_z", -9.8),
                sensor_data.get("gyro_roll", 0.0),
                sensor_data.get("gyro_pitch", 0.0),
                sensor_data.get("gyro_yaw", 0.0),
                sensor_data.get("pos_x", 0.0),
                sensor_data.get("pos_y", 0.0),
            ]

            self.csv_writer.writerow(row)
            self.record_count += 1
            if self.record_count % 10 == 0:
                self.file_handle.flush()

    def close(self):
        if not self.enabled:
            return

        with self.lock:
            if self.file_handle:
                self.file_handle.flush()
                self.file_handle.close()
                self.file_handle = None
                print(f"[+] Flight Logger stopped cleanly.")
                print(f"    - Saved Telemetry Records: {self.record_count}")
                print(f"    - Saved Frame Snapshots : {self.saved_frames_count}")
                print(f"    - Output Session Folder  : {self.session_dir}")
