# thermal_model.py

def update_temperature(current_temp, ambient_temp, power_on, dt_min, k, cooling_rate):
    """
    First-order thermal model for reefer container
    """
    if power_on:
        # Cooling ON
        if current_temp > ambient_temp:
            return current_temp
        return current_temp - cooling_rate * dt_min
    else:
        # Heat ingress
        return current_temp + k * (ambient_temp - current_temp) * dt_min
