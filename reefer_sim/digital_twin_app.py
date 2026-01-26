import sys
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QCheckBox
)
from PyQt5.QtCore import QTimer

# ---- Import your existing modules ----
from reefer_state import ReeferState
from thermal_model import update_temperature
from alarm_logic import check_alarms, update_spoilage_risk, classify_risk
from config import *
from data_logger import init_logger, log_data

# ---- Import UI components ----
from dashboard import PlotCanvas, LedIndicator, CircularGauge
from reefer_visual import ReeferView
import numpy as np
import joblib


class DigitalTwinApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Smart Reefer Container Digital Twin")
        self.setGeometry(50, 50, 1400, 800)
        
        # ---- Exhibition / Kiosk Mode ----
        self.showFullScreen()

        self.temp = SETPOINT_TEMP
        self.humidity = BASE_HUMIDITY
        self.ML_WARMUP_TIME = 15  # minutes
        self.MAX_POINTS = 300
        self.risk_index = 0.0
        self.time_min = 0
        self.early_fault_counter = 0
        self.EARLY_FAULT_CONFIRMATION_STEPS = 3
        self.SAFE_TEMP_LOW = -22.0
        self.SAFE_TEMP_HIGH = -18.0

        self.time_data = []
        self.temp_data = []
        self.hum_data = []
        self.early_fault_prob_data = []

        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_id = f"run_{timestamp}"
        
        self.log_filename = f"{self.run_id}_normal.csv"

        init_logger()

        # ---- Load Early Fault Detection Model ----
        self.early_fault_model = joblib.load("early_fault_random_forest.pkl")

        # Sliding window for ML features
        self.WINDOW_SIZE = 10
        self.feature_buffer = {
            "temp": [],
            "hum": [],
            "risk": []
        }

        self.init_ui()
        self.init_simulation_timer()

    # ---------------- UI ----------------
    def init_ui(self):
        main_layout = QHBoxLayout()

        # ===== LEFT: Reefer Visual =====
        self.reefer_view = ReeferView()
        main_layout.addWidget(self.reefer_view, 2)

        # ===== CENTER: Dashboard =====
        dashboard_layout = QVBoxLayout()

        # Gauges
        gauge_layout = QHBoxLayout()
        self.temp_gauge = CircularGauge("Temperature", -30, 10, "°C")
        self.hum_gauge = CircularGauge("Humidity", 0, 100, "%")
        gauge_layout.addWidget(self.temp_gauge)
        gauge_layout.addWidget(self.hum_gauge)
        dashboard_layout.addLayout(gauge_layout)

        # Plots
        self.temp_plot = PlotCanvas("Temperature Trend", "Temperature (°C)")
        self.hum_plot = PlotCanvas("Humidity Trend", "Humidity (%)")
        self.early_fault_plot = PlotCanvas("Early Fault Probability", "Probability")
        dashboard_layout.addWidget(self.early_fault_plot)
        dashboard_layout.addWidget(self.temp_plot)
        dashboard_layout.addWidget(self.hum_plot)

        # LEDs
        led_layout = QHBoxLayout()
        self.power_led = LedIndicator("⚡ POWER")
        self.door_led = LedIndicator("🚪 DOOR")
        self.risk_led = LedIndicator("⚠️ RISK")
        self.early_fault_led = LedIndicator("⏳ EARLY FAULT")
        led_layout.addWidget(self.power_led)
        led_layout.addWidget(self.door_led)
        led_layout.addWidget(self.risk_led)
        led_layout.addWidget(self.early_fault_led)

        dashboard_layout.addLayout(led_layout)

        main_layout.addLayout(dashboard_layout, 4)

        # ===== RIGHT: Fault Panel =====
        fault_box = QGroupBox("Fault Injection")
        fault_layout = QVBoxLayout()

        self.cb_power = QCheckBox("Power Failure")
        self.cb_door = QCheckBox("Door Open")
        self.cb_cooling = QCheckBox("Cooling Unit Failure")

        self.cb_power.stateChanged.connect(self.update_faults)
        self.cb_door.stateChanged.connect(self.update_faults)
        self.cb_cooling.stateChanged.connect(self.update_faults)

        fault_layout.addWidget(self.cb_power)
        fault_layout.addWidget(self.cb_door)
        fault_layout.addWidget(self.cb_cooling)
        fault_layout.addStretch()

        fault_box.setLayout(fault_layout)
        main_layout.addWidget(fault_box, 1)

        self.setLayout(main_layout)

    # ---------------- FAULTS ----------------
    def update_faults(self):
        ReeferState.power_on = not self.cb_power.isChecked()
        ReeferState.door_open = self.cb_door.isChecked()
        ReeferState.cooling_ok = not self.cb_cooling.isChecked()

        self.reefer_view.set_power(ReeferState.power_on)
        self.reefer_view.set_door(ReeferState.door_open)
        self.reefer_view.set_cooling(ReeferState.cooling_ok)

        faults = []

        if not ReeferState.power_on:
            faults.append("powerfail")
        if ReeferState.door_open:
            faults.append("dooropen")
        if not ReeferState.cooling_ok:
            faults.append("coolingfail")

        fault_tag = "_".join(faults) if faults else "normal"

        self.log_filename = f"{self.run_id}_{fault_tag}.csv"


    # ---------------- SIMULATION ----------------    
    def init_simulation_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.step_simulation)
        self.timer.start(1000)  # 1 sec = 1 min simulated

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

    def extract_ml_features(self):
        temp = np.array(self.feature_buffer["temp"])
        hum = np.array(self.feature_buffer["hum"])
        risk = np.array(self.feature_buffer["risk"])

        return np.array([[
            temp.mean(),
            temp[-1] - temp[0],      # temperature slope
            hum.mean(),
            hum[-1] - hum[0],        # humidity slope
            risk[-1] - risk[0],      # risk growth
            temp.std(),
            hum.std()
        ]])

    def step_simulation(self):
        # ---------- PHYSICS ----------
        power_on = ReeferState.power_on and ReeferState.cooling_ok

        self.temp = update_temperature(
            self.temp,
            ReeferState.ambient_temp,
            power_on,
            dt_min=1,
            k=HEAT_INGRESS_COEFF,
            cooling_rate=COOLING_RATE
        )

        # ---------- HUMIDITY DYNAMICS ----------
        if ReeferState.door_open:
            target_humidity = DOOR_OPEN_HUMIDITY
        else:
            target_humidity = HUMIDITY_RECOVERY

        self.humidity += HUMIDITY_RATE * (target_humidity - self.humidity)
        humidity = self.humidity

        # ---------- ALARMS & RISK ----------
        alarms = check_alarms(self.temp, humidity, power_on)
        self.risk_index = update_spoilage_risk(
            self.risk_index, self.temp, HIGH_TEMP_LIMIT, 1
        )
        risk_level = classify_risk(self.risk_index)

        # ---------- UPDATE ML FEATURE BUFFER ----------
        self.feature_buffer["temp"].append(self.temp)
        self.feature_buffer["hum"].append(humidity)
        self.feature_buffer["risk"].append(self.risk_index)

        for k in self.feature_buffer:
            if len(self.feature_buffer[k]) > self.WINDOW_SIZE:
                self.feature_buffer[k].pop(0)

        # ---------- PHYSICAL GUARDRAIL ----------
        within_safe_temp = self.SAFE_TEMP_LOW <= self.temp <= self.SAFE_TEMP_HIGH

        # ---------- EARLY FAULT PREDICTION ----------
        early_fault_pred = 0
        early_fault_prob = 0.0
        EARLY_FAULT_THRESHOLD = 0.8

        if (
            not within_safe_temp
            and len(self.feature_buffer["temp"]) == self.WINDOW_SIZE
            and self.time_min >= self.ML_WARMUP_TIME
        ):
            proba = self.early_fault_model.predict_proba(
                self.extract_ml_features()
            )

            early_fault_prob = proba[0, 1] if proba.shape[1] == 2 else proba[0, 0]

            if early_fault_prob > EARLY_FAULT_THRESHOLD:
                self.early_fault_counter += 1
            else:
                self.early_fault_counter = 0

            early_fault_pred = int(
                self.early_fault_counter >= self.EARLY_FAULT_CONFIRMATION_STEPS
            )
        else:
            # Guardrail active → suppress ML
            self.early_fault_counter = 0
            early_fault_pred = 0
            early_fault_prob = 0.0
        
        if self.time_min >= self.ML_WARMUP_TIME:
            self.early_fault_prob_data.append(early_fault_prob)
        else:
            self.early_fault_prob_data.append(0.0)

        if len(self.early_fault_prob_data) > self.MAX_POINTS:
            self.early_fault_prob_data = self.early_fault_prob_data[-self.MAX_POINTS:]

        # ---------- STORE DATA FOR PLOTS ----------
        self.time_data.append(self.time_min)
        self.temp_data.append(self.temp)
        self.hum_data.append(humidity)

        # Limit buffer size (keeps plotting fast)
        if len(self.time_data) > self.MAX_POINTS:
            self.time_data = self.time_data[-self.MAX_POINTS:]
            self.temp_data = self.temp_data[-self.MAX_POINTS:]
            self.hum_data = self.hum_data[-self.MAX_POINTS:]

        # ---------- UPDATE GAUGES ----------
        self.temp_gauge.set_value(self.temp)
        self.hum_gauge.set_value(humidity)

        # ---------- UPDATE LEDs ----------
        self.power_led.set_status(power_on)
        self.door_led.set_status(ReeferState.door_open)
        self.risk_led.set_status(
            risk_level != "LOW",
            "orange" if risk_level == "MEDIUM" else "red"
        )
        self.early_fault_led.set_status(
            early_fault_pred,
            color_on="orange"
        )

        # ---------- UPDATE TEMPERATURE PLOT ----------
        self.temp_plot.ax.clear()
        self.temp_plot.ax.plot(self.time_data, self.temp_data)
        self.temp_plot.ax.set_title("Temperature Trend")
        self.temp_plot.ax.set_ylabel("Temperature (°C)")
        self.temp_plot.ax.set_xlabel("Time (min)")
        self.temp_plot.ax.grid(True)
        self.temp_plot.draw()

        # ---------- UPDATE HUMIDITY PLOT ----------
        self.hum_plot.ax.clear()
        self.hum_plot.ax.plot(self.time_data, self.hum_data)
        self.hum_plot.ax.set_title("Humidity Trend")
        self.hum_plot.ax.set_ylabel("Humidity (%)")
        self.hum_plot.ax.set_xlabel("Time (min)")
        self.hum_plot.ax.grid(True)
        self.hum_plot.draw()

        # ---------- UPDATE EARLY FAULT PROBABILITY PLOT ----------
        self.early_fault_plot.ax.clear()
        self.early_fault_plot.ax.plot(
            self.time_data,
            self.early_fault_prob_data,
            color="orange"
        )
        self.early_fault_plot.ax.axhline(
            y=EARLY_FAULT_THRESHOLD,
            linestyle="--",
            linewidth=1
        )
        self.early_fault_plot.ax.set_title("Early Fault Probability")
        self.early_fault_plot.ax.set_ylabel("Probability")
        self.early_fault_plot.ax.set_xlabel("Time (min)")
        self.early_fault_plot.ax.set_ylim(0, 1)
        self.early_fault_plot.ax.grid(True)
        self.early_fault_plot.draw()

        # ---------- LOG DATA ----------
        log_data([
            self.run_id,
            self.time_min,
            round(self.temp, 2),
            round(humidity, 1),
            int(power_on),
            int(ReeferState.door_open),
            round(self.risk_index, 1),
            risk_level,
            int(not ReeferState.power_on),
            int(ReeferState.door_open),
            int(not ReeferState.cooling_ok)
        ])

        self.time_min += 1



# ---------------- RUN ----------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DigitalTwinApp()
    window.show()
    sys.exit(app.exec_())
