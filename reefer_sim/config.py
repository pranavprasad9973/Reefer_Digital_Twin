# config.py

# Time settings
TIME_STEP_SEC = 60           # 1 minute
SIM_DURATION_MIN = 240       # 4 hours

# Temperature settings (°C)
SETPOINT_TEMP = -20.0
HIGH_TEMP_LIMIT = -18.0
LOW_TEMP_LIMIT = -25.0
AMBIENT_TEMP = 35.0

# Thermal model
HEAT_INGRESS_COEFF = 0.002   # per minute
COOLING_RATE = 0.05          # °C per minute

# Humidity (%)
BASE_HUMIDITY = 75
HIGH_HUMIDITY_LIMIT = 90

# Risk thresholds (degree-minute)
RISK_LOW = 50
RISK_MEDIUM = 150

# Humidity dynamics
DOOR_OPEN_HUMIDITY = 95.0     # %
HUMIDITY_RECOVERY = 75.0     # %
HUMIDITY_RATE = 0.08         # per minute
