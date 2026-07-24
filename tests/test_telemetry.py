import unittest
from telemetry import TelemetryMapper
from gestures import LeftHandSignal

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

class TestTelemetry(unittest.TestCase):

    def test_altitude_throttle_relative_to_center(self):
        # Wrist above neutral launch height (y = 0.3 < 0.52) -> ascend (positive throttle)
        hand_up = MockHandLandmarks({0: MockLandmark(0.5, 0.3)})
        t_up = TelemetryMapper.calculate_throttle(hand_up, neutral_y=0.60)
        self.assertGreater(t_up, 0)

        # Wrist below neutral launch height (y = 0.75 > 0.68) -> descend (negative throttle)
        hand_down = MockHandLandmarks({0: MockLandmark(0.5, 0.75)})
        t_down = TelemetryMapper.calculate_throttle(hand_down, neutral_y=0.60)
        self.assertLess(t_down, 0)

    def test_speed_multipliers(self):
        # Pitch forward tilt (w0.z - m9.z = 0.25 > neutral 0.087 + 0.03)
        hand = MockHandLandmarks({
            0: MockLandmark(0.5, 0.7, z=0.10),
            9: MockLandmark(0.5, 0.7, z=0.00),
        })

        # Hover -> Roll/Pitch zeroed
        r_h, p_h, y_h, t_h = TelemetryMapper.process_dual_hand_telemetry(hand, hand, LeftHandSignal.HOVER)
        self.assertEqual(r_h, 0)
        self.assertEqual(p_h, 0)

        # Speed 4 (100%) vs Speed 1 (25%) -> pitch at Speed 4 > pitch at Speed 1
        _, p_s1, _, _ = TelemetryMapper.process_dual_hand_telemetry(hand, hand, LeftHandSignal.SPEED_1)
        _, p_s4, _, _ = TelemetryMapper.process_dual_hand_telemetry(hand, hand, LeftHandSignal.SPEED_4)
        self.assertGreater(p_s4, p_s1)

if __name__ == "__main__":
    unittest.main()
