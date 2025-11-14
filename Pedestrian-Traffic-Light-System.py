from machine import Pin, I2C, ADC, PWM
import ssd1306
import time

# Initializes I2C on the ESP32's default pins
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

# Initializes the 128x64 display
oled = ssd1306.SSD1306_I2C(128, 64, i2c)


#Defining Pins:

##Buttons
Bot1 = Pin(13,Pin.IN,Pin.PULL_UP) #Pedestrian Button
Bot2 = Pin(12,Pin.IN,Pin.PULL_UP) #Simulates Violation 

##Leds for traffic lights
T_ledR = Pin(25, Pin.OUT)
T_ledY= Pin(26, Pin.OUT)
T_ledG = Pin(33, Pin.OUT)

##Leds for RGB (Flash) 
F_ledR = Pin(14, Pin.OUT)
F_ledG = Pin(2, Pin.OUT)
F_ledB = Pin(15, Pin.OUT)

#Leds for Pedestrians
P_ledR = Pin(5, Pin.OUT)
P_ledG = Pin(18, Pin.OUT)

##Buzzer
buzzer = PWM(27)

##Potentiometer as traffic flow
adc = ADC(Pin(32))
adc.atten(ADC.ATTN_11DB)   # Reads until ~3.3V
adc.width(ADC.WIDTH_12BIT) # Resolution 0–4095

#Defining Variables:
Fines = 0

    
# ================== States ======================

# Traffic state machine
TRAFFIC_CAR_GREEN        = 0
TRAFFIC_WAIT_BEFORE_PED  = 1
TRAFFIC_PED_GREEN        = 2
TRAFFIC_TRANSITION_TO_CAR = 3
TRAFFIC_YELLOW_BEFORE_PED = 4


traffic_state = TRAFFIC_CAR_GREEN
traffic_state_start_ms = time.ticks_ms()
wait_before_ped_ms = 0
ped_green_ms = 0

# Buzzer state machine
BUZZER_IDLE              = 0
BUZZER_CONFIRMATION_BEEP = 1
BUZZER_CROSSING_BEEPS    = 2

buzzer_state = BUZZER_IDLE
buzzer_state_start_ms = time.ticks_ms()
last_beep_ms = time.ticks_ms()
beep_interval_ms = 400

# Interaction flags
pedestrian_request = False
crossing_active = False
confirmation_beep_pending = False

# Auxiliary timers
last_button_change_ms = time.ticks_ms()
last_button_level = 1  # HIGH 
last_lcd_update_ms = time.ticks_ms()
last_violation_check_ms = time.ticks_ms()

LCD_UPDATE_INTERVAL = 500   # ms
VIOLATION_CHECK_INTERVAL = 20  # ms


# ================== Auxiliary Functions ======================

def set_car_lights(red, yellow, green):
    T_ledR.value(1 if red else 0)
    T_ledY.value(1 if yellow else 0)
    T_ledG.value(1 if green else 0)

def set_ped_lights(red, green):
    P_ledR.value(1 if red else 0)
    P_ledG.value(1 if green else 0)

def read_traffic_flow_level():
    """
    Returns normalized value 0.0–1.0 based on ADC (potentiometer).
    In a real system, this is where the car flow measurement logic would come in.
    """
    raw = adc.read()  # 0..4095
    return min(max(raw / 4095.0, 0.0), 1.0)

def compute_wait_before_walk_ms():
    """
    10–60 seconds, proportional to flow
    (higher flow → longer wait).
    """
    flow = read_traffic_flow_level()
    min_ms = 10_000
    max_ms = 60_000
    return int(min_ms + (max_ms - min_ms) * flow)

def compute_ped_green_ms():
    """
    10–40 seconds, inversely proportional to flow
    (higher flow → shorter pedestrian time).
    """
    flow = read_traffic_flow_level()
    min_ms = 10_000
    max_ms = 40_000
    return int(max_ms - (max_ms - min_ms) * flow)

# --------- LCD Config -----------

def lcd_show_idle():
    # Clean the screen
    oled.fill(0)
    # Write text
    oled.text(" Press button ", 0, 0)
    oled.text("   to cross", 0, 20)
    # Refreshes the screen
    oled.show()

def lcd_show_wait(remaining_s):
    # Clean the screen
    oled.fill(0)
    # Write text
    oled.text("Wait to cross", 0, 0)
    msg = " Open in {}s".format(remaining_s)
    oled.text(msg, 0, 20)
    # Refreshes the screen
    oled.show()

def lcd_show_cross(remaining_s):
    # Clean the screen
    oled.fill(0)
    # Write text
    oled.text("Safe to cross ", 0, 0)
    msg = " Time left {}s".format(remaining_s)
    oled.text(msg, 0, 20)
    # Refreshes the screen
    oled.show()
    

# ================== State Machine: Button ======================

last_button_level = 1        # PULL_UP → starts loose
last_button_change_ms = 0
button_event_fired = False   # guarantees 1 event per click


def update_button(now_ms):
    global last_button_level, last_button_change_ms
    global pedestrian_request, confirmation_beep_pending
    global button_event_fired

    level = Bot1.value()      # 1 = released, 0 = pressed

    # Detects change (edge)
    if level != last_button_level:
        last_button_level = level
        last_button_change_ms = now_ms

    # Waits for stabilization (debounce)
    if time.ticks_diff(now_ms, last_button_change_ms) > 50:

        # Pressed AND has not yet registered event
        if level == 0 and not button_event_fired:
            pedestrian_request = True
            confirmation_beep_pending = True
            button_event_fired = True   # avoids multiple events

        # Released → releases for next click
        elif level == 1:
            button_event_fired = False


# ================== State Machine: Traffic ======================



def update_traffic_state(now_ms):
    global traffic_state, traffic_state_start_ms
    global wait_before_ped_ms, ped_green_ms
    global pedestrian_request, crossing_active

    # ===============================================================
    # 1. Traffic light green (initial state)
    # ===============================================================
    if traffic_state == TRAFFIC_CAR_GREEN:
        set_car_lights(red=False, yellow=False, green=True)
        set_ped_lights(red=True, green=False)
        crossing_active = False

        if pedestrian_request:
            wait_before_ped_ms = compute_wait_before_walk_ms()
            traffic_state_start_ms = now_ms
            traffic_state = TRAFFIC_WAIT_BEFORE_PED

    # ===============================================================
    # 2. Waiting for time between (10–60s)
    # ===============================================================
    elif traffic_state == TRAFFIC_WAIT_BEFORE_PED:
        set_car_lights(red=False, yellow=False, green=True)
        set_ped_lights(red=True, green=False)

        elapsed = time.ticks_diff(now_ms, traffic_state_start_ms)
        if elapsed >= wait_before_ped_ms:
            # Changes to "yello" state
            set_car_lights(red=False, yellow=True, green=False)
            traffic_state_start_ms = now_ms
            traffic_state = TRAFFIC_YELLOW_BEFORE_PED

    # ===============================================================
    #  3. Traffic light yellow
    # ===============================================================
    elif traffic_state == TRAFFIC_YELLOW_BEFORE_PED:
        set_car_lights(red=False, yellow=True, green=False)
        set_ped_lights(red=True, green=False)

        elapsed = time.ticks_diff(now_ms, traffic_state_start_ms)
        if elapsed >= 3000:  # 3s
            # Closes traffic 
            set_car_lights(red=True, yellow=False, green=False)
            set_ped_lights(red=False, green=True)

            ped_green_ms = compute_ped_green_ms()
            traffic_state_start_ms = now_ms
            traffic_state = TRAFFIC_PED_GREEN

            crossing_active = True
            pedestrian_request = False

    # ===============================================================
    # 4. Pedestrians crossing
    # ===============================================================
    elif traffic_state == TRAFFIC_PED_GREEN:
        pedestrian_request= False
        elapsed = time.ticks_diff(now_ms, traffic_state_start_ms)
        if elapsed >= ped_green_ms:
            set_ped_lights(red=True, green=False)
            set_car_lights(red=True, yellow=True, green=False)
            traffic_state_start_ms = now_ms
            traffic_state = TRAFFIC_TRANSITION_TO_CAR
            crossing_active = False

    # ===============================================================
    # 5. Last stage before green light (1s)
    # ===============================================================
    elif traffic_state == TRAFFIC_TRANSITION_TO_CAR:
        elapsed = time.ticks_diff(now_ms, traffic_state_start_ms)
        if elapsed >= 1000:
            set_car_lights(red=False, yellow=False, green=True)
            set_ped_lights(red=True, green=False)
            traffic_state = TRAFFIC_CAR_GREEN
            traffic_state_start_ms = now_ms


# ================== State Machine: buzzer ======================

beep_pulse_active = False
beep_pulse_start_ms = 0
BEEP_PULSE_DURATION = 50  # ms

def update_buzzer_state(now_ms):
    global buzzer_state, buzzer_state_start_ms
    global last_beep_ms, beep_interval_ms
    global confirmation_beep_pending, crossing_active
    global traffic_state, ped_green_ms, traffic_state_start_ms
    global beep_pulse_active, beep_pulse_start_ms

    # ============ MANAGE SIMPLE PWM PULSE (on/off) ============
    # If a pulse is active, we check if it is time to turn it off
    if beep_pulse_active:
        if time.ticks_diff(now_ms, beep_pulse_start_ms) >= BEEP_PULSE_DURATION:
            buzzer.duty(0)       # turn off the buzz
            beep_pulse_active = False

    # ===================== BUZZER MAIN  =============================

    if buzzer_state == BUZZER_IDLE:
        # Ensures it is turned off if it is not in pulse mode
        if not beep_pulse_active:
            buzzer.duty(0)

        # Priority: confirmation beep
        if confirmation_beep_pending:
            buzzer_state = BUZZER_CONFIRMATION_BEEP
            buzzer_state_start_ms = now_ms

        # If pedestrians are crossing, it enters “crossing beeps” mode.
        elif crossing_active and traffic_state == TRAFFIC_PED_GREEN:
            buzzer_state = BUZZER_CROSSING_BEEPS
            buzzer_state_start_ms = now_ms
            last_beep_ms = now_ms

    elif buzzer_state == BUZZER_CONFIRMATION_BEEP:
        
        elapsed = time.ticks_diff(now_ms, buzzer_state_start_ms)

        if elapsed < 100:
            buzzer.duty(512)  # beep turned on
        elif elapsed < 150:
            buzzer.duty(0)    # silence
        elif elapsed < 250:
            buzzer.duty(512)  # second beep
        else:
            buzzer.duty(0)
            confirmation_beep_pending = False
            buzzer_state = BUZZER_IDLE

    elif buzzer_state == BUZZER_CROSSING_BEEPS:
        # If the crossing is over, return to idle.
        if not crossing_active or traffic_state != TRAFFIC_PED_GREEN:
            if not beep_pulse_active:
                buzzer.duty(0)
            buzzer_state = BUZZER_IDLE
            return

        # Calculates the remaining time for the pedestrian green light
        elapsed = time.ticks_diff(now_ms, traffic_state_start_ms)
        remaining = ped_green_ms - elapsed if ped_green_ms > elapsed else 0

        max_interval = 400
        min_interval = 100
        if ped_green_ms > 0:
            ratio = remaining / ped_green_ms
            beep_interval_ms = int(min_interval + ratio * (max_interval - min_interval))
        else:
            beep_interval_ms = min_interval

        # Only start a new beep if:
        #  - the interval has passed
        #  - there is no pulse in progress
        if (not beep_pulse_active and
            time.ticks_diff(now_ms, last_beep_ms) >= beep_interval_ms):

            # Start a short PWM pulse (turn on the sound)
            buzzer.duty(512)          # turn on sound
            beep_pulse_active = True
            beep_pulse_start_ms = now_ms  # mark the start
            last_beep_ms = now_ms


# ================== LCD  ======================

def update_lcd(now_ms):
    global last_lcd_update_ms, fines
    global traffic_state, traffic_state_start_ms
    global wait_before_ped_ms, ped_green_ms

    if time.ticks_diff(now_ms, last_lcd_update_ms) < LCD_UPDATE_INTERVAL:
        return

    last_lcd_update_ms = now_ms

    if traffic_state == TRAFFIC_CAR_GREEN:
        lcd_show_idle()

    elif traffic_state == TRAFFIC_WAIT_BEFORE_PED:
        elapsed = time.ticks_diff(now_ms, traffic_state_start_ms)
        remaining = wait_before_ped_ms - elapsed if wait_before_ped_ms > elapsed else 0
        lcd_show_wait(remaining // 1000)

    elif traffic_state == TRAFFIC_PED_GREEN:
        elapsed = time.ticks_diff(now_ms, traffic_state_start_ms)
        remaining = ped_green_ms - elapsed if ped_green_ms > elapsed else 0
        lcd_show_cross(remaining // 1000)


# ================== Violation during red traffic light ======================

# Flash state machine
flash_active = False
flash_stage = 0
flash_timer_ms = 0

def start_flash_white():
    global flash_active, flash_stage, flash_timer_ms
    flash_active = True
    flash_stage = 0
    flash_timer_ms = time.ticks_ms()

def update_flash(now_ms):
    global flash_active, flash_stage, flash_timer_ms

    if not flash_active:
        return

    # Step 0: turns on (white light)
    if flash_stage == 0:
        F_ledR.value(1); F_ledG.value(1); F_ledB.value(1)
        flash_stage = 1
        flash_timer_ms = now_ms
        return

    # Step 1: waits 80ms, turns it off
    if flash_stage == 1:
        if time.ticks_diff(now_ms, flash_timer_ms) >= 80:
            F_ledR.value(0); F_ledG.value(0); F_ledB.value(0)
            flash_stage = 2
            flash_timer_ms = now_ms
        return

    # Step 2: Wait 80ms and repeat or finish
    if flash_stage == 2:
        if time.ticks_diff(now_ms, flash_timer_ms) >= 80:
            # Flash repeats 3x
            flash_stage = 3 if flash_stage == 2 else 0
            flash_active = False  # finish
        return

VIOLATION_DEBOUNCE_MS = 50

viol_last_level = 1            # assumes initially loose (PULL_UP)
viol_last_change_ms = 0
violation_handled = False      # guarantees 1 penalty per press



def update_violation(now_ms):
    global last_violation_check_ms, Fines
    global viol_last_level, viol_last_change_ms, violation_handled

    #  limit the refresh rate for violation check
    if time.ticks_diff(now_ms, last_violation_check_ms) < VIOLATION_CHECK_INTERVAL:
        return

    last_violation_check_ms = now_ms

    # Reads the current state of the button/sensor 
    level = Bot2.value()

    # Detects state change (edge)
    if level != viol_last_level:
        viol_last_change_ms = now_ms
        viol_last_level = level

    # Only consider the state after it has stabilized (debounce)
    if time.ticks_diff(now_ms, viol_last_change_ms) > VIOLATION_DEBOUNCE_MS:
        pressed = (viol_last_level == 0)  # True if Bot2 is pressed

        car_red_on = (T_ledR.value() == 1)

        # Button pressed, no bouncing, and not yet processed
        if pressed and car_red_on and not violation_handled:
            Fines += 1
            violation_handled = True
            start_flash_white()
            print("Fines:", Fines)

        # When you release the button, it releases to count a new violation in the future.
        if not pressed:
            violation_handled = False




# ================== Initial Setup ======================

def init_system():
    # Initial State: Traffic Green and Red for Pedestrians
    set_car_lights(False, False, True)
    set_ped_lights(True, False)
    #Buzz
    buzzer.duty(0)
    #Flash
    F_ledR.value(0)
    F_ledG.value(0)
    F_ledB.value(0)
    
    print("Traffic light system initialized! ")

# ================== MAIN LOOP ======================

def main():
    init_system()
    while True:
        now = time.ticks_ms()
        
        update_button(now)
        update_traffic_state(now)
        update_buzzer_state(now)
        update_lcd(now)
        update_violation(now)
        update_flash(now)
        
        time.sleep_ms(5)
        
        
    
# To run automatically when resetting.
if __name__ == "__main__":
    main()    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    