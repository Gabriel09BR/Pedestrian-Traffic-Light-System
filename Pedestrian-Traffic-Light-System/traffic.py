# traffic.py
import time
import hardware
import traffic_flow

# ======= Traffic States =======
TRAFFIC_CAR_GREEN = 0
TRAFFIC_WAIT_BEFORE_PED = 1
TRAFFIC_PED_GREEN = 2
TRAFFIC_TRANSITION_TO_CAR = 3
TRAFFIC_YELLOW_BEFORE_PED = 4

# ======= Internal State =======
traffic_state = TRAFFIC_CAR_GREEN
traffic_state_start_ms = time.ticks_ms()

wait_before_ped_ms = 0
ped_green_ms = 0

# Interaction flags
_pedestrian_request = False
_crossing_active = False


def init_traffic():
    """
    Initialize traffic state machine:
    - Cars start with green
    - Pedestrians start with red
    """
    global traffic_state, traffic_state_start_ms
    global wait_before_ped_ms, ped_green_ms
    global _pedestrian_request, _crossing_active

    traffic_state = TRAFFIC_CAR_GREEN
    traffic_state_start_ms = time.ticks_ms()
    wait_before_ped_ms = 0
    ped_green_ms = 0
    _pedestrian_request = False
    _crossing_active = False

    hardware.set_car_lights(False, False, True)   # green for cars
    hardware.set_ped_lights(True, False)          # red for pedestrians


def request_pedestrian():
    """Called when the pedestrian presses the crossing button."""
    global _pedestrian_request
    _pedestrian_request = True


def is_crossing_active():
    """True while pedestrians are allowed to cross the street."""
    return _crossing_active


def is_pedestrian_green():
    """True if the pedestrian light is green ."""
    return traffic_state == TRAFFIC_PED_GREEN


def is_car_red():
    """
    True if the car traffic light should be red.
    """
    return traffic_state in (TRAFFIC_PED_GREEN, TRAFFIC_TRANSITION_TO_CAR)


def get_state():
    """Return the current traffic state ."""
    return traffic_state


def get_wait_remaining_ms(now_ms):
    """
    Return remaining milliseconds in the WAIT_BEFORE_PED phase.
    Returns 0 if not in that state.
    """
    if traffic_state != TRAFFIC_WAIT_BEFORE_PED:
        return 0
    elapsed = time.ticks_diff(now_ms, traffic_state_start_ms)
    remaining = wait_before_ped_ms - elapsed
    if remaining < 0:
        remaining = 0
    return remaining


def get_ped_remaining_and_total_ms(now_ms):
    """
    Return (remaining_ms, total_ms) for the pedestrian green phase.
    If not in pedestrian green, remaining_ms = 0.
    """
    if traffic_state != TRAFFIC_PED_GREEN:
        return 0, ped_green_ms
    elapsed = time.ticks_diff(now_ms, traffic_state_start_ms)
    remaining = ped_green_ms - elapsed
    if remaining < 0:
        remaining = 0
    return remaining, ped_green_ms


def get_ped_ratio(now_ms):
    """
    Return remaining fraction of pedestrian green time (0.0–1.0).
    Used by the buzzer to adjust beep speed.
    """
    remaining, total = get_ped_remaining_and_total_ms(now_ms)
    if total <= 0:
        return 0.0
    return float(remaining) / float(total)


def update_traffic_state(now_ms):
    """
    Main state machine for the traffic lights.
    Called periodically in the main loop.
    """
    global traffic_state, traffic_state_start_ms
    global wait_before_ped_ms, ped_green_ms
    global _pedestrian_request, _crossing_active

    # 1. Car green (default state)
    if traffic_state == TRAFFIC_CAR_GREEN:
        hardware.set_car_lights(False, False, True)
        hardware.set_ped_lights(True, False)
        _crossing_active = False

        if _pedestrian_request:
            wait_before_ped_ms = traffic_flow.compute_wait_before_walk_ms()
            traffic_state_start_ms = now_ms
            traffic_state = TRAFFIC_WAIT_BEFORE_PED

    # 2. Waiting before pedestrian green (cars still green)
    elif traffic_state == TRAFFIC_WAIT_BEFORE_PED:
        hardware.set_car_lights(False, False, True)
        hardware.set_ped_lights(True, False)

        elapsed = time.ticks_diff(now_ms, traffic_state_start_ms)
        if elapsed >= wait_before_ped_ms:
            hardware.set_car_lights(False, True, False)  # yellow
            traffic_state_start_ms = now_ms
            traffic_state = TRAFFIC_YELLOW_BEFORE_PED

    # 3. Yellow phase before pedestrians
    elif traffic_state == TRAFFIC_YELLOW_BEFORE_PED:
        hardware.set_car_lights(False, True, False)
        hardware.set_ped_lights(True, False)

        elapsed = time.ticks_diff(now_ms, traffic_state_start_ms)
        if elapsed >= 3000:  # 3 seconds
            # Close car traffic, open for pedestrians
            hardware.set_car_lights(True, False, False)   # red for cars
            hardware.set_ped_lights(False, True)          # green for pedestrians

            ped_green_ms = traffic_flow.compute_ped_green_ms()
            traffic_state_start_ms = now_ms
            traffic_state = TRAFFIC_PED_GREEN

            _crossing_active = True
            _pedestrian_request = False

    # 4. Pedestrian green (crossing active)
    elif traffic_state == TRAFFIC_PED_GREEN:
        _pedestrian_request = False
        elapsed = time.ticks_diff(now_ms, traffic_state_start_ms)
        if elapsed >= ped_green_ms:
            hardware.set_ped_lights(True, False)          # red for pedestrians
            hardware.set_car_lights(True, False, False)    # red for cars
            traffic_state_start_ms = now_ms
            traffic_state = TRAFFIC_TRANSITION_TO_CAR
            _crossing_active = False

    # 5. Transition back to car green (1 second)
    elif traffic_state == TRAFFIC_TRANSITION_TO_CAR:
        elapsed = time.ticks_diff(now_ms, traffic_state_start_ms)
        if elapsed >= 1000:  # 1 second
            hardware.set_car_lights(False, False, True)   # green for cars
            hardware.set_ped_lights(True, False)          # red for pedestrians
            traffic_state = TRAFFIC_CAR_GREEN
            traffic_state_start_ms = now_ms

