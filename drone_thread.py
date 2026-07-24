import threading
import time
from state import SystemState, DroneState


class DroneWorkerThread:
    """
    Background worker thread running at 10-20 Hz to dispatch flight commands to CoDrone Edu hardware
    or log output in mock mode.
    """
    def __init__(self, mock_drone: bool = True, tick_rate_hz: float = 20.0):
        self.mock_drone = mock_drone
        self.interval = 1.0 / tick_rate_hz
        self.drone_state = DroneState()
        self.running = False
        self.thread = None
        self.drone_instance = None
        self._last_state = None

    def start(self):
        """Starts the background worker thread."""
        if not self.mock_drone:
            try:
                from codrone_edu.drone import Drone
                print("[*] Initializing CoDrone Edu hardware interface...")
                self.drone_instance = Drone()
                self.drone_instance.pair()
                print("[+] CoDrone Edu Bluetooth paired successfully!")
            except Exception as e:
                print(f"[!] CoDrone Edu initialization failed: {e}. Falling back to mock mode.")
                self.mock_drone = True
        else:
            print("[*] Starting Drone Worker Thread in MOCK DRONE mode.")

        self.running = True
        self.thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.thread.start()

    def _worker_loop(self):
        """Main periodic control tick loop."""
        while self.running:
            start_time = time.time()
            current_state = self.drone_state.get_state()
            roll, pitch, yaw, throttle = self.drone_state.get_flight_commands()

            # State Transition Handling
            if current_state != self._last_state:
                print(f"[*] Worker Thread State Shift: {self._last_state} -> {current_state}")
                if current_state == SystemState.MANUAL_CONTROL and self._last_state == SystemState.SEARCHING:
                    self._handle_takeoff()
                elif current_state == SystemState.SEARCHING and self._last_state == SystemState.MANUAL_CONTROL:
                    self._handle_land()
                elif current_state == SystemState.EMERGENCY_STOP:
                    self._handle_emergency_stop()
                self._last_state = current_state

            # Poll live or mock sensor telemetry
            self._poll_sensor_telemetry()

            # Flight Command Execution
            if current_state == SystemState.MANUAL_CONTROL:
                self._dispatch_flight_commands(roll, pitch, yaw, throttle)

            # Fixed tick rate sleep calculation
            elapsed = time.time() - start_time
            sleep_time = max(0.0, self.interval - elapsed)
            time.sleep(sleep_time)

    def _poll_sensor_telemetry(self):
        """Polls sensor readings from physical CoDrone Edu hardware or updates mock telemetry."""
        if not self.mock_drone and self.drone_instance:
            try:
                def safe_call(attr_names, default=0.0):
                    for name in attr_names:
                        if hasattr(self.drone_instance, name):
                            try:
                                fn = getattr(self.drone_instance, name)
                                val = fn()
                                if val is not None:
                                    return val
                            except Exception:
                                pass
                    return default

                sensor_data = {
                    "battery": safe_call(["get_battery"], 100),
                    "height_cm": safe_call(["get_height"], 0.0),
                    "temperature_c": safe_call(["get_drone_temp", "get_temperature"], 25.0),
                    "pressure_pa": safe_call(["get_pressure"], 101325.0),
                    "accel_x": safe_call(["get_x_accel", "get_accel_x"], 0.0),
                    "accel_y": safe_call(["get_y_accel", "get_accel_y"], 0.0),
                    "accel_z": safe_call(["get_z_accel", "get_accel_z"], -9.8),
                    "gyro_roll": safe_call(["get_roll", "get_x_angle"], 0.0),
                    "gyro_pitch": safe_call(["get_pitch", "get_y_angle"], 0.0),
                    "gyro_yaw": safe_call(["get_yaw", "get_z_angle"], 0.0),
                    "pos_x": safe_call(["get_pos_x", "get_position_x"], 0.0),
                    "pos_y": safe_call(["get_pos_y", "get_position_y"], 0.0),
                }
                self.drone_state.update_sensor_data(sensor_data)
            except Exception:
                pass
        else:
            # Mock Sensor Telemetry Simulation
            roll, pitch, yaw, throttle = self.drone_state.get_flight_commands()
            current_state = self.drone_state.get_state()

            current_sensors = self.drone_state.get_sensor_data()
            mock_height = current_sensors.get("height_cm", 0.0)

            if current_state == SystemState.MANUAL_CONTROL:
                mock_height = max(0.0, mock_height + (throttle * 0.05))
            else:
                mock_height = max(0.0, mock_height - 0.5)

            mock_sensors = {
                "battery": 98,
                "height_cm": round(mock_height, 2),
                "temperature_c": 26.5,
                "pressure_pa": 101320.0,
                "accel_x": round(pitch * 0.1, 2),
                "accel_y": round(roll * 0.1, 2),
                "accel_z": -9.81,
                "gyro_roll": float(roll),
                "gyro_pitch": float(pitch),
                "gyro_yaw": float(yaw),
                "pos_x": round(roll * 0.02, 2),
                "pos_y": round(pitch * 0.02, 2),
            }
            self.drone_state.update_sensor_data(mock_sensors)

    def _handle_takeoff(self):
        print("[+] DRONE WORKER: Initiating Takeoff Sequence!")
        if not self.mock_drone and self.drone_instance:
            try:
                self.drone_instance.takeoff()
            except Exception as e:
                print(f"[!] Hardware error during takeoff: {e}")

    def _handle_land(self):
        print("[+] DRONE WORKER: Initiating Safe Landing Sequence!")
        if not self.mock_drone and self.drone_instance:
            try:
                self.drone_instance.land()
            except Exception as e:
                print(f"[!] Hardware error during landing: {e}")

    def _handle_emergency_stop(self):
        print("[!] DRONE WORKER: EMERGENCY STOP ENGAGED! Halting motors & landing.")
        if not self.mock_drone and self.drone_instance:
            try:
                self.drone_instance.emergency_stop()
            except Exception as e:
                print(f"[!] Hardware error during emergency stop: {e}")

    def _dispatch_flight_commands(self, roll: int, pitch: int, yaw: int, throttle: int):
        if self.mock_drone:
            # Silence spam by printing only when commands change significantly or periodically
            pass
        elif self.drone_instance:
            try:
                self.drone_instance.set_roll(roll)
                self.drone_instance.set_pitch(pitch)
                self.drone_instance.set_yaw(yaw)
                self.drone_instance.set_throttle(throttle)
                self.drone_instance.move()
            except Exception as e:
                print(f"[!] Error dispatching flight commands: {e}")

    def stop(self):
        """Safely stops the worker thread and lands the drone."""
        print("[*] Stopping Drone Worker Thread...")
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)

        if not self.mock_drone and self.drone_instance:
            try:
                self.drone_instance.land()
                self.drone_instance.close()
                print("[+] CoDrone Edu hardware safely closed.")
            except Exception as e:
                print(f"[!] Error closing drone connection: {e}")
