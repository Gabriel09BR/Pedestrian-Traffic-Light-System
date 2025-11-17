# violation.py
import time
import hardware
import traffic
import flash_rgb

VIOLATION_CHECK_INTERVAL_MS = 20
VIOLATION_DEBOUNCE_MS = 50

_last_violation_check_ms = 0
_viol_last_level = 1
_viol_last_change_ms = 0
_violation_handled = False

_fines = 0  # number of recorded violations (cars crossing on red)


def init_violation():
    """Initialize violation detection state."""
    global _last_violation_check_ms, _viol_last_level
    global _viol_last_change_ms, _violation_handled, _fines

    _last_violation_check_ms = time.ticks_ms()
    _viol_last_level = hardware.Bot2.value()
    _viol_last_change_ms = time.ticks_ms()
    _violation_handled = False
    _fines = 0


def get_fines():
    """Return total number of recorded violations."""
    return _fines


def update_violation(now_ms):
    """
    Detect violations:
    - Bot2 simulates a vehicle crossing the stop line.
    - If pressed while car light is red, count a fine and flash RGB.
    """
    global _last_violation_check_ms, _viol_last_level
    global _viol_last_change_ms, _violation_handled, _fines

    # Limit check rate
    if time.ticks_diff(now_ms, _last_violation_check_ms) < VIOLATION_CHECK_INTERVAL_MS:
        return

    _last_violation_check_ms = now_ms

    level = hardware.Bot2.value()  # 1 = released, 0 = pressed

    # Edge detection
    if level != _viol_last_level:
        _viol_last_level = level
        _viol_last_change_ms = now_ms

    # After debounce time
    if time.ticks_diff(now_ms, _viol_last_change_ms) > VIOLATION_DEBOUNCE_MS:
        pressed = (_viol_last_level == 0)
        car_red_on = traffic.is_car_red()

        # Button pressed, car red, and not processed yet
        if pressed and car_red_on and not _violation_handled:
            _fines += 1
            _violation_handled = True
            flash_rgb.start_flash_white()
            print("Fines:", _fines)

        # On release, allow next violation to be counted
        if not pressed:
            _violation_handled = False
