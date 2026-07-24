import unittest
from gestures import is_thumbs_up, is_pointing, is_crossed_wrists, classify_left_hand, LeftHandSignal

class MockLandmark:
    def __init__(self, x, y, z=0.0):
        self.x = x
        self.y = y
        self.z = z

class MockHandLandmarks:
    def __init__(self, landmarks_dict):
        self.landmark = [MockLandmark(0.5, 0.5, 0.0) for _ in range(21)]
        if landmarks_dict:
            for idx, lm in landmarks_dict.items():
                self.landmark[idx] = lm

class TestGestures(unittest.TestCase):

    def test_point_up_launch_gesture_valid(self):
        # Point Up: Wrist at (0.5, 0.7), Index Tip at (0.5, 0.2), Index PIP at (0.5, 0.5)
        # Middle, Ring, Pinky folded
        landmarks = {
            0: MockLandmark(0.5, 0.7),
            2: MockLandmark(0.5, 0.6), 4: MockLandmark(0.5, 0.55),
            6: MockLandmark(0.5, 0.5), 8: MockLandmark(0.5, 0.2), # Index pointing UP
            10: MockLandmark(0.5, 0.5), 12: MockLandmark(0.5, 0.52), # Folded
            14: MockLandmark(0.5, 0.5), 16: MockLandmark(0.5, 0.52), # Folded
            18: MockLandmark(0.5, 0.5), 20: MockLandmark(0.5, 0.52), # Folded
        }
        hand = MockHandLandmarks(landmarks)
        self.assertTrue(is_pointing(hand))

    def test_right_hand_thumbs_up_valid(self):
        # Thumbs up: Wrist at (0.5, 0.7), Thumb MCP at (0.5, 0.5), Thumb Tip at (0.5, 0.2) -> Upwards
        # All non-thumb fingers folded (PIP at 0.5, Tip at 0.52 -> ratio <= 1.22)
        landmarks = {
            0: MockLandmark(0.5, 0.7),
            2: MockLandmark(0.5, 0.5), 4: MockLandmark(0.5, 0.2), # Thumb pointing UP
            6: MockLandmark(0.5, 0.5), 8: MockLandmark(0.5, 0.52), # Folded
            10: MockLandmark(0.5, 0.5), 12: MockLandmark(0.5, 0.52), # Folded
            14: MockLandmark(0.5, 0.5), 16: MockLandmark(0.5, 0.52), # Folded
            18: MockLandmark(0.5, 0.5), 20: MockLandmark(0.5, 0.52), # Folded
        }
        hand = MockHandLandmarks(landmarks)
        self.assertTrue(is_thumbs_up(hand))

    def test_right_hand_thumbs_up_with_fingers_open_invalid(self):
        # Thumbs up with open hand -> MUST BE FALSE
        landmarks = {
            0: MockLandmark(0.5, 0.7),
            2: MockLandmark(0.5, 0.5), 4: MockLandmark(0.5, 0.2),
            6: MockLandmark(0.5, 0.5), 8: MockLandmark(0.5, 0.2), # Extended
            10: MockLandmark(0.5, 0.5), 12: MockLandmark(0.5, 0.2), # Extended
        }
        hand = MockHandLandmarks(landmarks)
        self.assertFalse(is_thumbs_up(hand))

    def test_left_hand_speed_presets(self):
        h1 = MockHandLandmarks({
            0: MockLandmark(0.5, 0.7), 2: MockLandmark(0.5, 0.6), 4: MockLandmark(0.5, 0.55),
            6: MockLandmark(0.5, 0.5), 8: MockLandmark(0.5, 0.2),
            10: MockLandmark(0.5, 0.5), 12: MockLandmark(0.5, 0.52),
            14: MockLandmark(0.5, 0.5), 16: MockLandmark(0.5, 0.52),
            18: MockLandmark(0.5, 0.5), 20: MockLandmark(0.5, 0.52),
        })
        self.assertEqual(classify_left_hand(h1), LeftHandSignal.SPEED_1)

    def test_is_crossed_wrists(self):
        lw_uncrossed = MockLandmark(0.3, 0.5)
        rw_uncrossed = MockLandmark(0.7, 0.5)
        self.assertFalse(is_crossed_wrists(lw_uncrossed, rw_uncrossed))

        lw_crossed = MockLandmark(0.8, 0.5)
        rw_crossed = MockLandmark(0.2, 0.5)
        self.assertTrue(is_crossed_wrists(lw_crossed, rw_crossed))

if __name__ == "__main__":
    unittest.main()
