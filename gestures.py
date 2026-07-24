import math
from enum import Enum


class LeftHandSignal(Enum):
    HOVER = 0
    SPEED_1 = 1
    SPEED_2 = 2
    SPEED_3 = 3
    SPEED_4 = 4
    LAND = 5
    UNKNOWN = -1


def _euclidean_dist(p1, p2) -> float:
    """Calculates 3D Euclidean distance between two MediaPipe landmark points."""
    dx = p1.x - p2.x
    dy = p1.y - p2.y
    dz = getattr(p1, 'z', 0.0) - getattr(p2, 'z', 0.0)
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def is_finger_extended(wrist, pip, tip, ratio_threshold: float = 1.22) -> bool:
    """
    Determines if a finger is extended vs folded using rotation-invariant 3D Euclidean distances.
    Compares distance(wrist, tip) against distance(wrist, pip).
    """
    d_wrist_tip = _euclidean_dist(wrist, tip)
    d_wrist_pip = _euclidean_dist(wrist, pip)

    if d_wrist_pip < 1e-6:
        return False

    return (d_wrist_tip / d_wrist_pip) > ratio_threshold


def is_thumbs_up(hand_landmarks) -> bool:
    """
    Checks if hand landmark represents a valid Thumbs Up gesture:
    - Thumb tip (4) extended upwards above Thumb MCP (2) and Wrist (0).
    - All 4 non-thumb fingers (Index, Middle, Ring, Pinky) folded into a fist.
    """
    if not hand_landmarks or not hasattr(hand_landmarks, 'landmark'):
        return False

    landmarks = hand_landmarks.landmark
    if len(landmarks) < 21:
        return False

    wrist = landmarks[0]
    thumb_mcp = landmarks[2]
    thumb_tip = landmarks[4]

    # Thumb tip pointing upwards (smaller Y in MediaPipe coordinate space)
    thumb_upwards = (thumb_tip.y < thumb_mcp.y) and (thumb_tip.y < wrist.y)
    thumb_extended = _euclidean_dist(wrist, thumb_tip) > _euclidean_dist(wrist, thumb_mcp) * 1.15

    # All 4 non-thumb fingers must be folded into a fist
    index_up = is_finger_extended(wrist, landmarks[6], landmarks[8])
    middle_up = is_finger_extended(wrist, landmarks[10], landmarks[12])
    ring_up = is_finger_extended(wrist, landmarks[14], landmarks[16])
    pinky_up = is_finger_extended(wrist, landmarks[18], landmarks[20])

    all_four_fingers_folded = not (index_up or middle_up or ring_up or pinky_up)

    return thumb_upwards and thumb_extended and all_four_fingers_folded


def classify_left_hand(hand_landmarks) -> LeftHandSignal:
    """
    Classifies Left Hand gestures using rotation-invariant 3D landmark Euclidean distances:
    - Closed Fist (0 fingers extended, thumb neutral): Hover
    - 1 Finger Up (Index extended): Speed 1
    - 2 Fingers Up (Index + Middle extended): Speed 2
    - 3 Fingers Up (Index + Middle + Ring extended): Speed 3
    - 4 Fingers Up (Index + Middle + Ring + Pinky extended): Speed 4
    - Thumb Down (Thumb pointing down AND all 4 non-thumb fingers folded into a fist): Safe Land
    """
    if not hand_landmarks or not hasattr(hand_landmarks, 'landmark'):
        return LeftHandSignal.UNKNOWN

    landmarks = hand_landmarks.landmark
    if len(landmarks) < 21:
        return LeftHandSignal.UNKNOWN

    wrist = landmarks[0]
    thumb_mcp = landmarks[2]
    thumb_tip = landmarks[4]

    index_up = is_finger_extended(wrist, landmarks[6], landmarks[8])
    middle_up = is_finger_extended(wrist, landmarks[10], landmarks[12])
    ring_up = is_finger_extended(wrist, landmarks[14], landmarks[16])
    pinky_up = is_finger_extended(wrist, landmarks[18], landmarks[20])

    all_four_fingers_folded = not (index_up or middle_up or ring_up or pinky_up)

    # 1. THUMB DOWN LANDING SIGNAL:
    thumb_pointing_down = (thumb_tip.y > wrist.y) or (thumb_tip.y > thumb_mcp.y)
    thumb_extended = _euclidean_dist(wrist, thumb_tip) > _euclidean_dist(wrist, thumb_mcp) * 1.05

    if thumb_pointing_down and thumb_extended and all_four_fingers_folded:
        return LeftHandSignal.LAND

    # 2. SPEED PRESETS BASED ON EXTENDED FINGERS:
    extended_count = sum([index_up, middle_up, ring_up, pinky_up])

    if extended_count == 0:
        return LeftHandSignal.HOVER
    elif extended_count == 1 and index_up:
        return LeftHandSignal.SPEED_1
    elif extended_count == 2 and index_up and middle_up:
        return LeftHandSignal.SPEED_2
    elif extended_count == 3 and index_up and middle_up and ring_up:
        return LeftHandSignal.SPEED_3
    elif extended_count == 4:
        return LeftHandSignal.SPEED_4

    return LeftHandSignal.HOVER


def is_pointing(hand_landmarks) -> bool:
    """
    Evaluates whether right hand is performing a Point Up gesture (Takeoff / Launch command):
    - Index finger extended upwards (tip above PIP and wrist).
    - Middle, Ring, Pinky folded into fist.
    """
    if not hand_landmarks or not hasattr(hand_landmarks, 'landmark'):
        return False

    landmarks = hand_landmarks.landmark
    if len(landmarks) < 21:
        return False

    wrist = landmarks[0]
    index_pip = landmarks[6]
    index_tip = landmarks[8]

    # Index finger extended
    index_extended = is_finger_extended(wrist, index_pip, index_tip)

    # Middle, Ring, Pinky folded
    middle_folded = not is_finger_extended(wrist, landmarks[10], landmarks[12])
    ring_folded = not is_finger_extended(wrist, landmarks[14], landmarks[16])
    pinky_folded = not is_finger_extended(wrist, landmarks[18], landmarks[20])

    # Index tip pointing upwards relative to wrist
    index_pointing_up = (index_tip.y < index_pip.y) and (index_tip.y < wrist.y)

    return index_extended and middle_folded and ring_folded and pinky_folded and index_pointing_up


def is_crossed_wrists(left_wrist, right_wrist) -> bool:
    """Emergency Stop crossed-wrists killswitch."""
    if left_wrist is None or right_wrist is None:
        return False
    return left_wrist.x > right_wrist.x
