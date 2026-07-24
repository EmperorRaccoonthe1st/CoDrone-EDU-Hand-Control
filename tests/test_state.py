import unittest
import threading
from state import SystemState, DroneState

class TestDroneState(unittest.TestCase):

    def setUp(self):
        self.drone_state = DroneState()
        self.drone_state.set_state(SystemState.INIT)
        self.drone_state.update_flight_commands(0, 0, 0, 0)

    def test_singleton(self):
        s1 = DroneState()
        s2 = DroneState()
        self.assertIs(s1, s2)

    def test_state_transitions(self):
        self.drone_state.set_state(SystemState.SEARCHING)
        self.assertEqual(self.drone_state.get_state(), SystemState.SEARCHING)

        self.drone_state.set_state(SystemState.MANUAL_CONTROL)
        self.assertEqual(self.drone_state.get_state(), SystemState.MANUAL_CONTROL)

    def test_clamping_and_telemetry(self):
        self.drone_state.update_flight_commands(150, -200, 45, -80)
        roll, pitch, yaw, throttle = self.drone_state.get_flight_commands()
        self.assertEqual(roll, 100)
        self.assertEqual(pitch, -100)
        self.assertEqual(yaw, 45)
        self.assertEqual(throttle, -80)

    def test_emergency_stop_zeros_telemetry(self):
        self.drone_state.update_flight_commands(50, 50, 50, 50)
        self.drone_state.set_state(SystemState.EMERGENCY_STOP)
        self.assertEqual(self.drone_state.get_state(), SystemState.EMERGENCY_STOP)
        self.assertEqual(self.drone_state.get_flight_commands(), (0, 0, 0, 0))

    def test_concurrent_access(self):
        def reader():
            for _ in range(500):
                self.drone_state.get_state()
                self.drone_state.get_flight_commands()

        def writer():
            for i in range(500):
                self.drone_state.update_flight_commands(i % 100, -i % 100, i % 50, -i % 50)
                if i % 10 == 0:
                    self.drone_state.set_state(SystemState.MANUAL_CONTROL)

        threads = []
        for _ in range(5):
            threads.append(threading.Thread(target=reader))
            threads.append(threading.Thread(target=writer))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertIn(self.drone_state.get_state(), [SystemState.INIT, SystemState.SEARCHING, SystemState.MANUAL_CONTROL, SystemState.EMERGENCY_STOP])

if __name__ == "__main__":
    unittest.main()
