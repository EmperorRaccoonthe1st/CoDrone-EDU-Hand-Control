import os
import csv
import tempfile
import unittest
from flight_logger import FlightLogger
from gestures import LeftHandSignal
from state import DroneState, SystemState


class MockLandmark:
    def __init__(self, x, y, z=0.0):
        self.x = x
        self.y = y
        self.z = z


class MockHandLandmarks:
    def __init__(self, landmarks_dict):
        self.landmark = [MockLandmark(0.5, 0.5) for _ in range(21)]
        for idx, lm in landmarks_dict.items():
            self.landmark[idx] = lm


class TestFlightLogger(unittest.TestCase):

    def test_logger_file_creation_and_recording(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            logger = FlightLogger(enabled=True, log_dir=tmp_dir)
            self.assertTrue(os.path.exists(logger.filepath))

            mock_left = MockHandLandmarks({0: MockLandmark(0.5, 0.4)})
            mock_right = MockHandLandmarks({0: MockLandmark(0.6, 0.8, z=0.0), 9: MockLandmark(0.6, 0.6, z=-0.1)})
            sensor_data = {
                "battery": 95,
                "height_cm": 120.5,
                "temperature_c": 27.2,
                "pressure_pa": 101315.0,
                "accel_x": 0.1,
                "accel_y": 0.0,
                "accel_z": -9.81,
                "gyro_roll": 5.0,
                "gyro_pitch": -2.0,
                "gyro_yaw": 0.0,
                "pos_x": 10.2,
                "pos_y": 15.4,
            }

            import numpy as np
            mock_img = np.zeros((100, 100, 3), dtype=np.uint8)

            logger.log_frame(
                frame_idx=5,
                system_state="MANUAL_CONTROL",
                left_signal=LeftHandSignal.SPEED_2,
                left_hand_landmarks=mock_left,
                right_hand_landmarks=mock_right,
                flight_commands=(10, 20, 0, 30),
                sensor_data=sensor_data,
                neutral_params={"pitch_dz": 0.087},
                image_frame=mock_img
            )

            logger.close()

            self.assertTrue(os.path.exists(logger.frames_dir))
            saved_frame_path = os.path.join(logger.frames_dir, "frame_000005.jpg")
            self.assertTrue(os.path.exists(saved_frame_path))

            with open(logger.filepath, "r", encoding="utf-8") as f:
                reader = list(csv.reader(f))
                self.assertEqual(len(reader), 2)  # Header + 1 record row
                header = reader[0]
                self.assertIn("timestamp_iso", header)
                self.assertIn("pitch_delta", header)
                self.assertIn("saved_frame", header)

                record = reader[1]
                self.assertEqual(record[2], "5")  # frame_index
                self.assertEqual(record[4], "MANUAL_CONTROL")
                self.assertEqual(record[5], "SPEED_2")
                self.assertEqual(record[13], "20")  # command_pitch

    def test_drone_state_sensor_updates(self):
        state = DroneState()
        sensors = {"battery": 88, "height_cm": 150.0}
        state.update_sensor_data(sensors)

        data = state.get_sensor_data()
        self.assertEqual(data["battery"], 88)
        self.assertEqual(data["height_cm"], 150.0)


if __name__ == "__main__":
    unittest.main()
