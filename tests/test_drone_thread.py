import unittest
import time
from state import SystemState, DroneState
from drone_thread import DroneWorkerThread

class TestDroneWorkerThread(unittest.TestCase):

    def setUp(self):
        self.drone_state = DroneState()
        self.drone_state.set_state(SystemState.SEARCHING)

    def test_mock_worker_thread_lifecycle(self):
        worker = DroneWorkerThread(mock_drone=True, tick_rate_hz=20.0)
        worker.start()
        self.assertTrue(worker.running)
        self.assertTrue(worker.thread.is_alive())

        # Test state transition to MANUAL_CONTROL
        self.drone_state.set_state(SystemState.MANUAL_CONTROL)
        self.drone_state.update_flight_commands(20, -10, 5, 30)
        time.sleep(0.1)

        # Test state transition to SEARCHING (Safe Landing)
        self.drone_state.set_state(SystemState.SEARCHING)
        time.sleep(0.1)
        self.assertEqual(self.drone_state.get_flight_commands(), (0, 0, 0, 0))

        # Test state transition to EMERGENCY_STOP
        self.drone_state.set_state(SystemState.EMERGENCY_STOP)
        time.sleep(0.1)

        worker.stop()
        self.assertFalse(worker.running)
        self.assertFalse(worker.thread.is_alive())

if __name__ == "__main__":
    unittest.main()
