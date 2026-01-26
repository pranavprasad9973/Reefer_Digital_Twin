# alarm_logic.py

def check_alarms(temp, humidity, power_on):
    alarms = {
        "HIGH_TEMP": temp > -18,
        "LOW_TEMP": temp < -25,
        "HIGH_HUMIDITY": humidity > 90,
        "POWER_FAIL": not power_on
    }
    return alarms


def update_spoilage_risk(risk_index, temp, safe_temp, dt_min):
    if temp > safe_temp:
        risk_index += (temp - safe_temp) * dt_min
    return risk_index


def classify_risk(risk):
    if risk < 50:
        return "LOW"
    elif risk < 150:
        return "MEDIUM"
    else:
        return "HIGH"
