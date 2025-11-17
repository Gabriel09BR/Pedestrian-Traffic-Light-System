# flash_rgb.py
import time
import hardware

_flash_active = False
_flash_stage = 0
_flash_timer_ms = 0


def init_flash():
    """Initialize RGB flash state."""
    global _flash_active, _flash_stage, _flash_timer_ms
    _flash_active = False
    _flash_stage = 0
    _flash_timer_ms = time.ticks_ms()
    hardware.F_ledR.value(0)
    hardware.F_ledG.value(0)
    hardware.F_ledB.value(0)


def start_flash_white():
    """
    Start a short white flash (when a violation is detected).
    """
    global _flash_active, _flash_stage, _flash_timer_ms
    _flash_active = True
    _flash_stage = 0
    _flash_timer_ms = time.ticks_ms()


def update_flash(now_ms):
    """
    Update RGB flash state machine.
    Called periodically in the main loop.
    """
    global _flash_active, _flash_stage, _flash_timer_ms

    if not _flash_active:
        return

    # Stage 0: turn white ON
    if _flash_stage == 0:
        hardware.F_ledR.value(1)
        hardware.F_ledG.value(1)
        hardware.F_ledB.value(1)
        _flash_stage = 1
        _flash_timer_ms = now_ms
        return

    # Stage 1: wait 80 ms, then turn OFF
    if _flash_stage == 1:
        if time.ticks_diff(now_ms, _flash_timer_ms) >= 80:
            hardware.F_ledR.value(0)
            hardware.F_ledG.value(0)
            hardware.F_ledB.value(0)
            _flash_stage = 2
            _flash_timer_ms = now_ms
        return

    # Stage 2: end sequence
    if _flash_stage == 2:
        _flash_active = False
