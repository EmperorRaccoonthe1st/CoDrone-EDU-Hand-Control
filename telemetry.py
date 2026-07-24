import math
from gestures import LeftHandSignal, is_thumbs_up


def clamp(val: int, min_val: int = -100, max_val: int = 100) -> int:
    return max(min_val, min(max_val, int(val)))


class TelemetryMapper:
    """
    Translates Dual-Hand Landmarks into normalized flight telemetry:
    - Left Hand: Controls Speed Multipliers (Hover 0%, Speed 1 25%, Speed 2 50%, Speed 3 75%, Speed 4 100%).
    - Right Hand: Virtual 3D Joystick (Thumbs Up handle controlling Elevation/Throttle via height, Pitch/Roll/Yaw via orientation).
    """

    SPEED_MULTIPLIERS = {
        LeftHandSignal.HOVER: 0.0,
        LeftHandSignal.SPEED_1: 0.25,
        LeftHandSignal.SPEED_2: 0.50,
        LeftHandSignal.SPEED_3: 0.75,
        LeftHandSignal.SPEED_4: 1.00,
        LeftHandSignal.LAND: 0.0,
        LeftHandSignal.UNKNOWN: 0.50,
    }

    @staticmethod
    def calculate_throttle(left_hand_landmarks, neutral_y: float = 0.60) -> int:
        """
        Elevation / Throttle derived from Left Hand Wrist screen height relative to left hand neutral launch height.
        Left Wrist above neutral (wrist_y < neutral_y - 0.08): Ascend (Positive throttle).
        Left Wrist below neutral (wrist_y > neutral_y + 0.08): Descend (Negative throttle).
        Deadzone range [neutral_y - 0.08, neutral_y + 0.08]: 0 throttle (Neutral hover).
        """
        if not left_hand_landmarks or not hasattr(left_hand_landmarks, 'landmark'):
            return 0

        wrist_y = left_hand_landmarks.landmark[0].y
        upper_deadzone = neutral_y - 0.08
        lower_deadzone = neutral_y + 0.08

        if wrist_y < upper_deadzone:
            return clamp((upper_deadzone - wrist_y) * 400)
        elif wrist_y > lower_deadzone:
            return clamp((lower_deadzone - wrist_y) * 400)
        return 0

    @staticmethod
    def calculate_pitch(right_hand_landmarks, speed_mult: float = 1.0, neutral_pitch_dz: float = +0.087) -> int:
        """
        Whole-Hand Joystick Pitch (Tilt Forward / Tilt Backward):
        Derived from 3D Z-depth offset between Wrist (0) and Middle MCP (9) compared to launch baseline.
        Tilt Forward (Positive Pitch), Tilt Backward (Negative Pitch).
        Uses artificial high-gain calibration for backward pitch to overcome 2D camera perspective limitations:
        - Forward Tilt (d_pitch > +0.005): Deadzone threshold +0.005, Multiplier 3600 * speed_mult
        - Backward Tilt (d_pitch < -0.002): Deadzone threshold -0.002, Multiplier 16000 * speed_mult (snappy 4.4x boost)
        """
        landmarks = right_hand_landmarks.landmark
        w0 = landmarks[0]
        m9 = landmarks[9]

        pitch_dz = w0.z - m9.z
        d_pitch = pitch_dz - neutral_pitch_dz

        if d_pitch > 0.005:
            effective_d = d_pitch - 0.005
            return clamp(effective_d * 3600 * speed_mult)
        elif d_pitch < -0.002:
            effective_d = d_pitch + 0.002
            return clamp(effective_d * 16000 * speed_mult)
        return 0

    @staticmethod
    def calculate_roll(right_hand_landmarks, speed_mult: float = 1.0, neutral_roll_dx: float = -0.042) -> int:
        """
        Whole-Hand Joystick Roll (Bank Left / Bank Right):
        Derived from Thumb Tip (4) X position relative to Wrist (0) compared to launch baseline.
        Bank Left (Negative Roll), Bank Right (Positive Roll).
        Uses tight 0.015 deadzone and 2000 scaling multiplier for responsive lateral control.
        """
        landmarks = right_hand_landmarks.landmark
        w0 = landmarks[0]
        t4 = landmarks[4]

        roll_dx = t4.x - w0.x
        d_roll = roll_dx - neutral_roll_dx

        if d_roll > 0.015:
            effective_d = d_roll - 0.015
            return clamp(effective_d * 2000 * speed_mult)
        elif d_roll < -0.015:
            effective_d = d_roll + 0.015
            return clamp(effective_d * 2000 * speed_mult)
        return 0

    @staticmethod
    def calculate_yaw(right_hand_landmarks, speed_mult: float = 1.0, neutral_yaw_dx: float = +0.032) -> int:
        """
        Whole-Hand Joystick Yaw: TEMPORARILY DISABLED for fine-tuning Pitch & Roll control.
        Always returns 0.
        """
        return 0

    @classmethod
    def process_dual_hand_telemetry(cls, right_hand_landmarks, left_hand_landmarks_or_signal=None, left_hand_signal: LeftHandSignal = None, neutral_params: dict = None) -> tuple[int, int, int, int]:
        """
        Processes dual-hand inputs to output (roll, pitch, yaw, throttle):
        - Left Hand: Speed presets, safe landing, and Height/Throttle.
        - Right Hand: 3D Whole-Hand Joystick Pitch and Roll.
        Supports both 2-arg (right_landmarks, signal) and 3-arg (right_landmarks, left_landmarks, signal) signatures.
        """
        if isinstance(left_hand_landmarks_or_signal, LeftHandSignal):
            signal = left_hand_landmarks_or_signal
            left_lms = None
        else:
            left_lms = left_hand_landmarks_or_signal
            signal = left_hand_signal if left_hand_signal is not None else LeftHandSignal.SPEED_2

        if neutral_params is None:
            neutral_params = {
                'roll_dx': -0.042,
                'pitch_dz': +0.087,
                'yaw_dx': +0.032,
                'left_throttle_y': 0.60,
            }

        speed_mult = cls.SPEED_MULTIPLIERS.get(signal, 0.50)

        n_roll_dx = neutral_params.get('roll_dx', -0.042)
        n_pitch_dz = neutral_params.get('pitch_dz', +0.087)
        n_left_y = neutral_params.get('left_throttle_y', 0.60)

        # Calculate Elevation / Throttle from LEFT Hand Height relative to left launch neutral
        throttle = cls.calculate_throttle(left_lms, neutral_y=n_left_y)

        if signal == LeftHandSignal.HOVER or not right_hand_landmarks or not hasattr(right_hand_landmarks, 'landmark'):
            return (0, 0, 0, throttle)

        pitch = cls.calculate_pitch(right_hand_landmarks, speed_mult, neutral_pitch_dz=n_pitch_dz)
        roll = cls.calculate_roll(right_hand_landmarks, speed_mult, neutral_roll_dx=n_roll_dx)
        yaw = 0  # Yaw temporarily disabled

        return (roll, pitch, yaw, throttle)
