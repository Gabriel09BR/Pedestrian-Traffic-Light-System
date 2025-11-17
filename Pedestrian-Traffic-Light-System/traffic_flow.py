# traffic_flow.py
import hardware


def read_traffic_flow_level():
    """
    Returns a normalized value 0.0–1.0 based on ADC reading.
    In a real system, this would represent vehicle flow intensity.
    """
    raw = hardware.adc.read()  
    value = raw / 4095.0
    if value < 0.0:
        value = 0.0
    if value > 1.0:
        value = 1.0
    return value


def compute_wait_before_walk_ms():
    """
    Return the waiting time before pedestrians can cross.
    Range: 10–60 seconds, proportional to traffic flow
    (higher flow → longer waiting time).
    """
    flow = read_traffic_flow_level()
    min_ms = 10_000
    max_ms = 60_000
    return int(min_ms + (max_ms - min_ms) * flow)


def compute_ped_green_ms():
    """
    Return the green time for pedestrians.
    Range: 10–40 seconds, inversely proportional to traffic flow
    (higher flow → shorter pedestrian green time).
    """
    flow = read_traffic_flow_level()
    min_ms = 10_000
    max_ms = 40_000
    return int(max_ms - (max_ms - min_ms) * flow)
