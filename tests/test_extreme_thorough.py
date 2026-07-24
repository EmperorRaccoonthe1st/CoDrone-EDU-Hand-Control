import unittest
import threading
import time
import math
import random

from state import SystemState, DroneState
from gestures import is_pointing, is_crossed_wrists, classify_left_hand, LeftHandSignal
from telemetry import TelemetryMapper, clamp
from drone_thread import DroneWorkerThread


class MockLandmark:
    def __init__(self, x, y, z=0.0):
        self.x = x
        self.y = y
        self.z = z


class MockHandLandmarks:
    def __init__(self, landmarks_dict=None):
        self.landmark = [MockLandmark(0.5, 0.5, 0.0) for _ in range(21)]
        if landmarks_dict:
            for idx, lm in landmarks_dict.items():
                self.landmark[idx] = lm


class TestExtremeThorough(unittest.TestCase):

    def test_extreme_thread_concurrency(self):
        drone_state = DroneState()
        exceptions = []

        def worker_writer(thread_id):
            try:
                for i in range(400):
                    roll = random.randint(-500, 500)
                    pitch = random.randint(-500, 500)
                    yaw = random.randint(-500, 500)
                    throttle = random.randint(-500, 500)
                    drone_state.update_flight_commands(roll, pitch, yaw, throttle)

                    if i % 25 == 0:
                        states = list(SystemState)
                        drone_state.set_state(random.choice(states))
            except Exception as e:
                exceptions.append((thread_id, e))

        def worker_reader(thread_id):
            try:
                for _ in range(400):
                    drone_state.get_state()
                    r, p, y, t = drone_state.get_flight_commands()
                    self.assertTrue(-100 <= r <= 100)
                    self.assertTrue(-100 <= p <= 100)
                    self.assertTrue(-100 <= y <= 100)
                    self.assertTrue(-100 <= t <= 100)
            except Exception as e:
                exceptions.append((thread_id, e))

        threads = []
        for i in range(25):
            threads.append(threading.Thread(target=worker_writer, args=(f"writer-{i}",)))
            threads.append(threading.Thread(target=worker_reader, args=(f"reader-{i}",)))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(exceptions), 0, f"Thread exceptions occurred: {exceptions}")

    def test_emergency_stop_override_race_condition(self):
        drone_state = DroneState()
        for _ in range(100):
            drone_state.set_state(SystemState.MANUAL_CONTROL)
            drone_state.update_flight_commands(100, 100, 100, 100)
            drone_state.set_state(SystemState.EMERGENCY_STOP)

            commands = drone_state.get_flight_commands()
            self.assertEqual(commands, (0, 0, 0, 0))

    def test_gestures_malformed_input(self):
        self.assertFalse(is_pointing(None))
        self.assertFalse(is_pointing("invalid_object"))
        self.assertFalse(is_pointing(MockHandLandmarks()))

        self.assertEqual(classify_left_hand(None), LeftHandSignal.UNKNOWN)
        self.assertEqual(classify_left_hand("invalid_object"), LeftHandSignal.UNKNOWN)
        
        truncated_hand = MockHandLandmarks()
        truncated_hand.landmark = truncated_hand.landmark[:10]
        self.assertEqual(classify_left_hand(truncated_hand), LeftHandSignal.UNKNOWN)
        self.assertFalse(is_pointing(truncated_hand))

        self.assertFalse(is_crossed_wrists(None, None))

    def test_all_left_hand_speed_signal_combinations(self):
        # 1. Closed Fist -> HOVER
        fist = MockHandLandmarks({
            0: MockLandmark(0.5, 0.7), 2: MockLandmark(0.5, 0.6), 4: MockLandmark(0.5, 0.55),
            6: MockLandmark(0.5, 0.5), 8: MockLandmark(0.5, 0.52),
            10: MockLandmark(0.5, 0.5), 12: MockLandmark(0.5, 0.52),
            14: MockLandmark(0.5, 0.5), 16: MockLandmark(0.5, 0.52),
            18: MockLandmark(0.5, 0.5), 20: MockLandmark(0.5, 0.52),
        })
        self.assertEqual(classify_left_hand(fist), LeftHandSignal.HOVER)

        # 2. 1 Finger Up (Index) -> SPEED_1
        sp1 = MockHandLandmarks({
            0: MockLandmark(0.5, 0.7), 2: MockLandmark(0.5, 0.6), 4: MockLandmark(0.5, 0.55),
            6: MockLandmark(0.5, 0.5), 8: MockLandmark(0.5, 0.2),
            10: MockLandmark(0.5, 0.5), 12: MockLandmark(0.5, 0.52),
            14: MockLandmark(0.5, 0.5), 16: MockLandmark(0.5, 0.52),
            18: MockLandmark(0.5, 0.5), 20: MockLandmark(0.5, 0.52),
        })
        self.assertEqual(classify_left_hand(sp1), LeftHandSignal.SPEED_1)

        # 3. 2 Fingers Up (Index + Middle) -> SPEED_2
        sp2 = MockHandLandmarks({
            0: MockLandmark(0.5, 0.7), 2: MockLandmark(0.5, 0.6), 4: MockLandmark(0.5, 0.55),
            6: MockLandmark(0.5, 0.5), 8: MockLandmark(0.5, 0.2),
            10: MockLandmark(0.5, 0.5), 12: MockLandmark(0.5, 0.2),
            14: MockLandmark(0.5, 0.5), 16: MockLandmark(0.5, 0.52),
            18: MockLandmark(0.5, 0.5), 20: MockLandmark(0.5, 0.52),
        })
        self.assertEqual(classify_left_hand(sp2), LeftHandSignal.SPEED_2)

        # 4. Thumb Down WITH ALL FINGERS FOLDED IN FIST (Sideways hand) -> LAND
        thumb_down_fist = MockHandLandmarks({
            0: MockLandmark(0.3, 0.5),
            2: MockLandmark(0.35, 0.55),
            4: MockLandmark(0.35, 0.8), # Thumb Down
            6: MockLandmark(0.4, 0.5), 8: MockLandmark(0.42, 0.5),
            10: MockLandmark(0.4, 0.52), 12: MockLandmark(0.42, 0.52),
            14: MockLandmark(0.4, 0.54), 16: MockLandmark(0.42, 0.54),
            18: MockLandmark(0.4, 0.56), 20: MockLandmark(0.42, 0.56),
        })
        self.assertEqual(classify_left_hand(thumb_down_fist), LeftHandSignal.LAND)

    def test_telemetry_extreme_boundaries(self):
        hand_extreme = MockHandLandmarks({
            0: MockLandmark(-10.0, -10.0),
            5: MockLandmark(10.0, 10.0),
            8: MockLandmark(-10.0, -10.0),
            9: MockLandmark(10.0, 10.0),
            17: MockLandmark(10.0, 10.0),
        })

        roll, pitch, yaw, throttle = TelemetryMapper.process_dual_hand_telemetry(hand_extreme, LeftHandSignal.SPEED_4)
        self.assertTrue(-100 <= roll <= 100)
        self.assertTrue(-100 <= pitch <= 100)
        self.assertTrue(-100 <= yaw <= 100)
        self.assertTrue(-100 <= throttle <= 100)

    def test_worker_thread_rapid_restart_stress(self):
        for i in range(20):
            worker = DroneWorkerThread(mock_drone=True, tick_rate_hz=50.0)
            worker.start()
            self.assertTrue(worker.running)
            time.sleep(0.02)
            worker.stop()
            self.assertFalse(worker.running)


if __name__ == "__main__":
    unittest.main()
