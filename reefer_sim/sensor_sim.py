# sensor_sim.py

import random

def simulate_power_status(time_min):
    return False if 60 <= time_min <= 120 else True

def simulate_door_status(time_min):
    return True if 150 <= time_min <= 165 else False

def simulate_humidity(door_open):
    base = 75
    return base + random.uniform(10, 20) if door_open else base + random.uniform(-3, 3)
