# dashboard.py

import sys
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame
)
from PyQt5.QtCore import QTimer, Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PyQt5.QtGui import QPainter, QPen, QColor, QFont
from PyQt5.QtCore import QRectF
import math

LOG_FILE = "logs/reefer_log.csv"

ICON_POWER = "⚡"
ICON_DOOR = "🚪"
ICON_RISK = "⚠️"

class CircularGauge(QWidget):
    def __init__(self, title, min_val, max_val, unit):
        super().__init__()
        self.title = title
        self.min_val = min_val
        self.max_val = max_val
        self.unit = unit
        self.value = min_val
        self.setMinimumSize(220, 220)

    def set_value(self, value):
        self.value = max(self.min_val, min(self.max_val, value))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # ---------- Force Square Area ----------
        side = min(self.width(), self.height())
        margin = 20
        arc_rect = QRectF(
            (self.width() - side) / 2 + margin,
            (self.height() - side) / 2 + margin,
            side - 2 * margin,
            side - 2 * margin
        )

        pen_width = side * 0.08

        # ---------- Background Arc ----------
        pen_bg = QPen(QColor("#e5e7eb"), pen_width)
        pen_bg.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_bg)
        painter.drawArc(arc_rect, 225 * 16, 270 * 16)

        # ---------- Value Arc ----------
        span_angle = int(
            (self.value - self.min_val)
            / (self.max_val - self.min_val)
            * 270
        )

        pen_val = QPen(self.get_color(), pen_width)
        pen_val.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_val)
        painter.drawArc(arc_rect, 225 * 16, -span_angle * 16)

        # ---------- Title (TOP) ----------
        painter.setPen(Qt.black)
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.drawText(
            QRectF(0, 5, self.width(), 20),
            Qt.AlignCenter,
            self.title
        )

        # ---------- Value (CENTER) ----------
        painter.setFont(QFont("Arial", 16, QFont.Bold))
        painter.drawText(
            QRectF(0, self.height() / 2 - 20, self.width(), 40),
            Qt.AlignCenter,
            f"{self.value:.1f} {self.unit}"
        )

    def get_color(self):
        ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        if ratio < 0.6:
            return QColor("#16a34a")   # green
        elif ratio < 0.8:
            return QColor("#f59e0b")   # orange
        else:
            return QColor("#dc2626")   # red

class LedIndicator(QLabel):
    def __init__(self, label_text):
        super().__init__()

        self.label_text = label_text
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(50)
        self.setStyleSheet(self.off_style())

    def on_style(self, color):
        return f"""
            QLabel {{
                background-color: {color};
                border-radius: 15px;
                color: white;
                font-weight: bold;
                font-size: 14px;
                padding: 8px;
            }}
        """

    def off_style(self):
        return """
            QLabel {
                background-color: #9ca3af;
                border-radius: 15px;
                color: white;
                font-weight: bold;
                font-size: 14px;
                padding: 8px;
            }
        """

    def set_status(self, status, color_on="green"):
        if status:
            self.setText(f"{self.label_text}: ON")
            self.setStyleSheet(self.on_style(color_on))
        else:
            self.setText(f"{self.label_text}: OFF")
            self.setStyleSheet(self.off_style())


class PlotCanvas(FigureCanvas):
    def __init__(self, title, ylabel):
        self.fig = Figure(facecolor="#f4f6f8")
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)

        self.ax.set_title(title)
        self.ax.set_ylabel(ylabel)
        self.ax.set_xlabel("Time (min)")
        self.ax.grid(True)


class ReeferDashboard(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Smart Reefer Container Monitoring")
        self.setGeometry(100, 100, 1200, 700)
        self.setStyleSheet("background-color: #f4f6f8;")

        self.init_ui()
        self.init_timer()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # ---------- Header ----------
        header = QLabel("SMART REEFER CONTAINER MONITORING SYSTEM")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("""
            font-size: 22px;
            font-weight: bold;
            padding: 12px;
            background-color: #1f2933;
            color: white;
        """)
        main_layout.addWidget(header)

        # ---------- Middle Layout ----------
        mid_layout = QHBoxLayout()

        # ===== LEFT SIDE: Gauges + Plots =====
        left_layout = QVBoxLayout()

        # --- Gauges Row ---
        gauge_layout = QHBoxLayout()

        self.temp_gauge = CircularGauge("Temperature", -30, 10, "°C")
        self.hum_gauge = CircularGauge("Humidity", 0, 100, "%")

        gauge_layout.addWidget(self.temp_gauge)
        gauge_layout.addWidget(self.hum_gauge)

        left_layout.addLayout(gauge_layout)

        # --- Trend Plots ---
        self.temp_plot = PlotCanvas("Temperature Trend", "Temperature (°C)")
        self.hum_plot = PlotCanvas("Humidity Trend", "Humidity (%)")

        left_layout.addWidget(self.temp_plot)
        left_layout.addWidget(self.hum_plot)

        # ===== RIGHT SIDE: Status LEDs =====
        status_layout = QVBoxLayout()
        status_layout.setAlignment(Qt.AlignTop)

        self.power_led = LedIndicator(f"{ICON_POWER} POWER")
        self.door_led = LedIndicator(f"{ICON_DOOR} DOOR")
        self.risk_led = LedIndicator(f"{ICON_RISK} RISK")

        status_layout.addWidget(self.power_led)
        status_layout.addWidget(self.door_led)
        status_layout.addWidget(self.risk_led)

        # ---------- Combine Layouts ----------
        mid_layout.addLayout(left_layout, 3)
        mid_layout.addLayout(status_layout, 1)

        main_layout.addLayout(mid_layout)
        self.setLayout(main_layout)


    def status_label(self, text):
        label = QLabel(text)
        label.setFrameStyle(QFrame.Panel | QFrame.Raised)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            padding: 15px;
            margin: 10px;
            background-color: white;
            border-radius: 6px;
        """)
        return label

    def init_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_dashboard)
        self.timer.start(1000)  # refresh every 1 second

    def update_dashboard(self):
        try:
            df = pd.read_csv(LOG_FILE)
        except Exception:
            return

        if df.empty:
            return

        # ----- Update Plots -----
        self.temp_plot.ax.clear()
        self.hum_plot.ax.clear()

        self.temp_plot.ax.plot(df["Time(min)"], df["Temp(C)"])
        self.hum_plot.ax.plot(df["Time(min)"], df["Humidity(%)"])

        self.temp_plot.ax.set_title("Temperature Trend")
        self.hum_plot.ax.set_title("Humidity Trend")
        self.temp_plot.ax.set_ylabel("Temperature (°C)")
        self.hum_plot.ax.set_ylabel("Humidity (%)")
        self.temp_plot.ax.grid(True)
        self.hum_plot.ax.grid(True)

        self.temp_plot.draw()
        self.hum_plot.draw()

        # ----- Latest Values -----
        latest = df.iloc[-1]

        self.update_status_led(self.power_led, latest["Power"])
        self.update_status_led(self.door_led, latest["Door"])
        self.update_risk_led(latest["Risk_Level"])

        self.temp_gauge.set_value(latest["Temp(C)"])
        self.hum_gauge.set_value(latest["Humidity(%)"])

    def update_status_led(self, led, status):
        led.set_status(status, color_on="green")


    def update_risk_led(self, risk):
        if risk == "LOW":
            self.risk_led.setText(f"{ICON_RISK} RISK: LOW")
            self.risk_led.setStyleSheet(self.risk_led.on_style("green"))
        elif risk == "MEDIUM":
            self.risk_led.setText(f"{ICON_RISK} RISK: MEDIUM")
            self.risk_led.setStyleSheet(self.risk_led.on_style("orange"))
        else:
            self.risk_led.setText(f"{ICON_RISK} RISK: HIGH")
            self.risk_led.setStyleSheet(self.risk_led.on_style("red"))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ReeferDashboard()
    window.show()
    sys.exit(app.exec_())
