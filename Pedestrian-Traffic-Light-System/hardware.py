# hardware.py
from machine import Pin, I2C, ADC, PWM
import ssd1306

# ========= Pin Config =========

# Buttons
BOT1_PIN = 13  # Pedestrian button
BOT2_PIN = 12  # Violation sensor / button

# Traffic lights (cars)
T_RED_PIN = 25
T_YELLOW_PIN = 26
T_GREEN_PIN = 33

# RGB flash (for violation)
F_RED_PIN = 14
F_GREEN_PIN = 2
F_BLUE_PIN = 15

# Pedestrian lights
P_RED_PIN = 5
P_GREEN_PIN = 18

# Buzzer
BUZZER_PIN = 27

# Potentiometer (traffic flow simulation)
ADC_PIN = 32

# ========= Peripheral Objects =========

# I2C and OLED will be initialized later 
i2c = None
oled = None

# Buttons
Bot1 = Pin(BOT1_PIN, Pin.IN, Pin.PULL_UP)
Bot2 = Pin(BOT2_PIN, Pin.IN, Pin.PULL_UP)

# Traffic LEDs
T_ledR = Pin(T_RED_PIN, Pin.OUT)
T_ledY = Pin(T_YELLOW_PIN, Pin.OUT)
T_ledG = Pin(T_GREEN_PIN, Pin.OUT)

# Flash RGB LEDs
F_ledR = Pin(F_RED_PIN, Pin.OUT)
F_ledG = Pin(F_GREEN_PIN, Pin.OUT)
F_ledB = Pin(F_BLUE_PIN, Pin.OUT)

# Pedestrian LEDs
P_ledR = Pin(P_RED_PIN, Pin.OUT)
P_ledG = Pin(P_GREEN_PIN, Pin.OUT)

# Buzzer (PWM)
buzzer = PWM(Pin(BUZZER_PIN))

# ADC (potentiometer / traffic flow)
adc = ADC(Pin(ADC_PIN))



def init_oled():
    """
    Initialize I2C and OLED.
    """
    global i2c, oled
    try:
        i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
        # If your display uses address 0x3D instead of 0x3C, change addr=0x3D
        oled = ssd1306.SSD1306_I2C(128, 64, i2c)
        print("OLED initialized successfully")
    except OSError as e:
        print("Failed to initialize OLED:", e)
        oled = None


def set_car_lights(red, yellow, green):
    """Control the 3 LEDs of the car traffic light."""
    T_ledR.value(1 if red else 0)
    T_ledY.value(1 if yellow else 0)
    T_ledG.value(1 if green else 0)


def set_ped_lights(red, green):
    """Control the 2 LEDs of the pedestrian traffic light."""
    P_ledR.value(1 if red else 0)
    P_ledG.value(1 if green else 0)


def init_outputs():
    """Initialize outputs in a safe default state."""
    set_car_lights(False, False, False)
    set_ped_lights(True, False)
    F_ledR.value(0)
    F_ledG.value(0)
    F_ledB.value(0)
    buzzer.duty(0)
