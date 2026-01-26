# main_sim.py

from config import *
from thermal_model import update_temperature
from sensor_sim import *
from alarm_logic import *
from data_logger import *
from reefer_state import ReeferState


def run_simulation():

    temp = SETPOINT_TEMP
    risk_index = 0.0
    time_min = 0

    log_file = "reefer_log.csv"
    init_logger(log_file)

    while time_min <= SIM_DURATION_MIN:

        power_on = ReeferState.power_on and ReeferState.cooling_ok
        door_open = simulate_door_status(time_min)

        temp = update_temperature(
            temp,
            AMBIENT_TEMP,
            power_on,
            dt_min=1,
            k=HEAT_INGRESS_COEFF,
            cooling_rate=COOLING_RATE
        )

        humidity = BASE_HUMIDITY
        if ReeferState.door_open:
            humidity += 15

        alarms = check_alarms(temp, humidity, power_on)
        risk_index = update_spoilage_risk(risk_index, temp, HIGH_TEMP_LIMIT, 1)
        risk_level = classify_risk(risk_index)

        log_data(log_file, [
            time_min, round(temp, 2), round(humidity, 1),
            power_on, door_open, round(risk_index, 1), risk_level
        ])

        time_min += 1

    print("Simulation complete. Data logged to", log_file)


if __name__ == "__main__":
    run_simulation()
