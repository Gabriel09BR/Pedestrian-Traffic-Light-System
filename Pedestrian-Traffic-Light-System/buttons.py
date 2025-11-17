# buttons.py
import time
import hardware
import traffic
import buzzer

DEBOUNCE_MS = 50

_last_button_level = 1       
_last_button_change_ms = 0
_button_event_fired = False   # guarantees 1 event per click


def init_buttons():
    global _last_button_level, _last_button_change_ms, _button_event_fired
    _last_button_level = hardware.Bot1.value()
    _last_button_change_ms = time.ticks_ms()
    _button_event_fired = False


def update_button(now_ms):
    """
    Debounced button handling for the pedestrian button (Bot1).
    When a valid press is detected:
      - requests pedestrian crossing
      - triggers confirmation beep
    """
    global _last_button_level, _last_button_change_ms
    global _button_event_fired

    level = hardware.Bot1.value()  # 1 = released, 0 = pressed

    # Edge detection
    if level != _last_button_level:
        _last_button_level = level
        _last_button_change_ms = now_ms

    # After debounce time
    if time.ticks_diff(now_ms, _last_button_change_ms) > DEBOUNCE_MS:

        # Pressed and not yet handled
        if level == 0 and not _button_event_fired:
            traffic.request_pedestrian()
            buzzer.request_confirmation_beep()
            _button_event_fired = True

        # Released → allow next click
        elif level == 1:
            _button_event_fired = False
