# buzzer.py
import time
import hardware
import traffic

# ======= Buzzer States =======
BUZZER_IDLE = 0
BUZZER_CONFIRMATION_BEEP = 1
BUZZER_CROSSING_BEEPS = 2

buzzer_state = BUZZER_IDLE
buzzer_state_start_ms = time.ticks_ms()

last_beep_ms = time.ticks_ms()
beep_interval_ms = 400

# Short PWM pulse 
BEEP_PULSE_DURATION = 50  # ms
_beep_pulse_active = False
_beep_pulse_start_ms = 0

# Confirmation beep flag
_confirmation_beep_pending = False


def init_buzzer():
    """
    Initialize buzzer state and ensure PWM is off.
    """
    global buzzer_state, buzzer_state_start_ms
    global last_beep_ms, beep_interval_ms
    global _beep_pulse_active, _beep_pulse_start_ms
    global _confirmation_beep_pending

    buzzer_state = BUZZER_IDLE
    buzzer_state_start_ms = time.ticks_ms()
    last_beep_ms = time.ticks_ms()
    beep_interval_ms = 400
    _beep_pulse_active = False
    _beep_pulse_start_ms = 0
    _confirmation_beep_pending = False
    hardware.buzzer.duty(0)


def request_confirmation_beep():
    """Called when the pedestrian button is pressed (double beep)."""
    global _confirmation_beep_pending
    _confirmation_beep_pending = True


def _handle_pulse(now_ms):
    """
    Manage short PWM pulses for crossing beeps.
    """
    global _beep_pulse_active, _beep_pulse_start_ms

    if _beep_pulse_active:
        if time.ticks_diff(now_ms, _beep_pulse_start_ms) >= BEEP_PULSE_DURATION:
            hardware.buzzer.duty(0)
            _beep_pulse_active = False


def update_buzzer_state(now_ms):
    """
    Update buzzer state machine.
    Called periodically in the main loop.
    """
    global buzzer_state, buzzer_state_start_ms
    global last_beep_ms, beep_interval_ms
    global _beep_pulse_active, _beep_pulse_start_ms
    global _confirmation_beep_pending

    # Manage short on/off PWM pulses
    _handle_pulse(now_ms)

    if buzzer_state == BUZZER_IDLE:
        # Ensure it is OFF when no pulse is active
        if not _beep_pulse_active:
            hardware.buzzer.duty(0)

        # Confirmation beep
        if _confirmation_beep_pending:
            buzzer_state = BUZZER_CONFIRMATION_BEEP
            buzzer_state_start_ms = now_ms

        # If pedestrians are crossing, start crossing beep mode
        elif traffic.is_crossing_active() and traffic.is_pedestrian_green():
            buzzer_state = BUZZER_CROSSING_BEEPS
            buzzer_state_start_ms = now_ms
            last_beep_ms = now_ms

    elif buzzer_state == BUZZER_CONFIRMATION_BEEP:
        elapsed = time.ticks_diff(now_ms, buzzer_state_start_ms)

        if elapsed < 100:
            hardware.buzzer.duty(512)  # first beep
        elif elapsed < 150:
            hardware.buzzer.duty(0)    # silence
        elif elapsed < 250:
            hardware.buzzer.duty(512)  # second beep
        else:
            hardware.buzzer.duty(0)
            _confirmation_beep_pending = False
            buzzer_state = BUZZER_IDLE

    elif buzzer_state == BUZZER_CROSSING_BEEPS:
        # If crossing is over, go back to idle
        if not traffic.is_crossing_active() or not traffic.is_pedestrian_green():
            if not _beep_pulse_active:
                hardware.buzzer.duty(0)
            buzzer_state = BUZZER_IDLE
            return

        # Adjust beep interval based on remaining pedestrian time
        ratio = traffic.get_ped_ratio(now_ms)
        max_interval = 400
        min_interval = 100
        beep_interval_ms = int(min_interval + ratio * (max_interval - min_interval))

        # Start a new beep pulse if enough time has passed
        if (not _beep_pulse_active and
                time.ticks_diff(now_ms, last_beep_ms) >= beep_interval_ms):

            hardware.buzzer.duty(512)          # turn on sound
            _beep_pulse_active = True
            _beep_pulse_start_ms = now_ms
            last_beep_ms = now_ms
