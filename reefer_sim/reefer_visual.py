import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QGraphicsView, QGraphicsScene, QGraphicsRectItem,
    QGraphicsTextItem, QCheckBox, QGroupBox
)
from PyQt5.QtGui import QBrush, QPen, QPainter
from PyQt5.QtCore import Qt
from reefer_state import ReeferState



# ------------------ REEFER VISUAL ------------------

class ReeferView(QGraphicsView):
    def __init__(self):
        super().__init__()

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.setRenderHint(QPainter.Antialiasing)
        self.setMinimumSize(600, 260)

        self.draw_container()

    def draw_container(self):
        # Container body
        container = QGraphicsRectItem(0, 0, 500, 200)
        container.setBrush(QBrush(Qt.lightGray))
        container.setPen(QPen(Qt.black, 2))
        self.scene.addItem(container)

        # Cooling unit
        self.cooling_unit = QGraphicsRectItem(10, 50, 80, 100)
        self.cooling_unit.setBrush(QBrush(Qt.green))
        self.scene.addItem(self.cooling_unit)

        cooling_text = QGraphicsTextItem("COOLING\nUNIT")
        cooling_text.setPos(15, 80)
        self.scene.addItem(cooling_text)

        # Cargo
        cargo = QGraphicsRectItem(110, 30, 300, 140)
        cargo.setBrush(QBrush(Qt.white))
        cargo.setPen(QPen(Qt.black, 1, Qt.DashLine))
        self.scene.addItem(cargo)

        cargo_text = QGraphicsTextItem("CARGO SPACE")
        cargo_text.setPos(220, 90)
        self.scene.addItem(cargo_text)

        # Door
        self.door = QGraphicsRectItem(420, 30, 70, 140)
        self.door.setBrush(QBrush(Qt.darkGray))
        self.scene.addItem(self.door)

        door_text = QGraphicsTextItem("DOOR")
        door_text.setPos(435, 90)
        self.scene.addItem(door_text)

        # Power cable
        self.power = QGraphicsRectItem(-30, 90, 30, 20)
        self.power.setBrush(QBrush(Qt.green))
        self.scene.addItem(self.power)

        power_text = QGraphicsTextItem("POWER")
        power_text.setPos(-30, 65)
        self.scene.addItem(power_text)

    # ---------- STATE UPDATE METHODS ----------

    def set_power(self, on: bool):
        self.power.setBrush(QBrush(Qt.green if on else Qt.red))

    def set_door(self, open_: bool):
        self.door.setBrush(QBrush(Qt.red if open_ else Qt.darkGray))

    def set_cooling(self, ok: bool):
        self.cooling_unit.setBrush(QBrush(Qt.green if ok else Qt.red))


# ------------------ MAIN WINDOW ------------------

class ReeferSimulator(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Reefer Container Fault Simulator")
        self.setGeometry(150, 150, 850, 350)

        self.reefer_view = ReeferView()

        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()

        # ----- Left: Reefer Visual -----
        main_layout.addWidget(self.reefer_view, 3)

        # ----- Right: Fault Injection Panel -----
        fault_box = QGroupBox("Fault Injection Panel")
        fault_box.setStyleSheet("font-weight: bold;")
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

    # ---------- FAULT HANDLING ----------
    def update_faults(self):
        ReeferState.power_on = not self.cb_power.isChecked()
        ReeferState.door_open = self.cb_door.isChecked()
        ReeferState.cooling_ok = not self.cb_cooling.isChecked()

        self.reefer_view.set_power(ReeferState.power_on)
        self.reefer_view.set_door(ReeferState.door_open)
        self.reefer_view.set_cooling(ReeferState.cooling_ok)



# ------------------ RUN ------------------

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ReeferSimulator()
    window.show()
    sys.exit(app.exec_())
