# display_oled.py
import time
import hardware
import traffic

LCD_UPDATE_INTERVAL_MS = 500
_last_lcd_update_ms = 0


def init_display():
    """Initialize OLED display and show idle message."""
    global _last_lcd_update_ms
    _last_lcd_update_ms = time.ticks_ms()
    # Try to init OLED
    hardware.init_oled()
    # If OLED is not available, just don't crash
    if hardware.oled is not None:
        show_idle()
    else:
        print("Display not available, skipping OLED drawing")


def show_idle():
    if hardware.oled is None:
        return
    hardware.oled.fill(0)
    hardware.oled.text(" Press button ", 0, 0)
    hardware.oled.text("   to cross",   0, 20)
    hardware.oled.show()


def show_wait(remaining_s):
    if hardware.oled is None:
        return
    hardware.oled.fill(0)
    hardware.oled.text("Wait to cross", 0, 0)
    msg = " Opens in {}s".format(remaining_s)
    hardware.oled.text(msg, 0, 20)
    hardware.oled.show()


def show_cross(remaining_s):
    if hardware.oled is None:
        return
    hardware.oled.fill(0)
    hardware.oled.text("Safe to cross ", 0, 0)
    msg = " Time left {}s".format(remaining_s)
    hardware.oled.text(msg, 0, 20)
    hardware.oled.show()


def update_lcd(now_ms):
    """
    Periodically update the OLED display according to the current
    traffic state and remaining times.
    """
    global _last_lcd_update_ms

    if hardware.oled is None:
        return  # OLED not available, do nothing

    if time.ticks_diff(now_ms, _last_lcd_update_ms) < LCD_UPDATE_INTERVAL_MS:
        return

    _last_lcd_update_ms = now_ms
    state = traffic.get_state()

    if state == traffic.TRAFFIC_CAR_GREEN:
        show_idle()

    elif state == traffic.TRAFFIC_WAIT_BEFORE_PED:
        remaining_ms = traffic.get_wait_remaining_ms(now_ms)
        show_wait(remaining_ms // 1000)

    elif state == traffic.TRAFFIC_PED_GREEN:
        remaining_ms, _ = traffic.get_ped_remaining_and_total_ms(now_ms)
        show_cross(remaining_ms // 1000)
