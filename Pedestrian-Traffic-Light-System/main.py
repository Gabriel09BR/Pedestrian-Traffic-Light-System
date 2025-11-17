# main.py
import time
import hardware
import traffic
import buzzer
import buttons
import display_oled
import flash_rgb
import violation


def init_system():
    """
    Initialize all modules and set initial state
    for the pedestrian traffic light system.
    """
    hardware.init_outputs()
    traffic.init_traffic()
    buzzer.init_buzzer()
    buttons.init_buttons()
    display_oled.init_display()
    flash_rgb.init_flash()
    violation.init_violation()
    print("Pedestrian traffic light system initialized!")


def main():
    init_system()
    while True:
        now = time.ticks_ms()

        buttons.update_button(now)
        traffic.update_traffic_state(now)
        buzzer.update_buzzer_state(now)
        display_oled.update_lcd(now)
        violation.update_violation(now)
        flash_rgb.update_flash(now)

        time.sleep_ms(5)


if __name__ == "__main__":
    main()
