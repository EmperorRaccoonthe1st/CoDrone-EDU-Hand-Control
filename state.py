import threading
from enum import Enum

class SystemState(Enum):
    INIT = 0
    SEARCHING = 1
    MANUAL_CONTROL = 2
    EMERGENCY_STOP = 3

class DroneState:
    """Thread-safe Singleton state machine for sharing state & telemetry between vision and drone threads."""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DroneState, cls).__new__(cls)
                cls._instance._state = SystemState.INIT
                cls._instance._roll = 0
                cls._instance._pitch = 0
                cls._instance._yaw = 0
                cls._instance._throttle = 0
                cls._instance._sensor_data = {
                    "battery": 100,
                    "height_cm": 0.0,
                    "temperature_c": 25.0,
                    "pressure_pa": 101325.0,
                    "accel_x": 0.0,
                    "accel_y": 0.0,
                    "accel_z": 0.0,
                    "gyro_roll": 0.0,
                    "gyro_pitch": 0.0,
                    "gyro_yaw": 0.0,
                    "pos_x": 0.0,
                    "pos_y": 0.0,
                }
        return cls._instance

    @staticmethod
    def _clamp(value: int, min_val: int = -100, max_val: int = 100) -> int:
        return max(min_val, min(max_val, int(value)))

    def update_flight_commands(self, roll: int, pitch: int, yaw: int, throttle: int):
        with self._lock:
            self._roll = self._clamp(roll)
            self._pitch = self._clamp(pitch)
            self._yaw = self._clamp(yaw)
            self._throttle = self._clamp(throttle)

    def get_flight_commands(self) -> tuple[int, int, int, int]:
        with self._lock:
            return (self._roll, self._pitch, self._yaw, self._throttle)

    def update_sensor_data(self, sensor_dict: dict):
        with self._lock:
            self._sensor_data.update(sensor_dict)

    def get_sensor_data(self) -> dict:
        with self._lock:
            return dict(self._sensor_data)

    def set_state(self, new_state: SystemState):
        with self._lock:
            self._state = new_state
            if new_state != SystemState.MANUAL_CONTROL:
                # Instantly zero telemetry on non-flight states (SEARCHING, EMERGENCY_STOP, INIT)
                self._roll = 0
                self._pitch = 0
                self._yaw = 0
                self._throttle = 0

    def get_state(self) -> SystemState:
        with self._lock:
            return self._state
