import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QLabel, QLineEdit, QSlider, QMessageBox
from PyQt5.QtCore import Qt
from dynamixel_sdk import *

class DynamixelWizard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enhanced Dynamixel Wizard")
        self.setGeometry(100, 100, 500, 400)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.port_selector = QComboBox()
        self.port_selector.addItems(["/dev/ttyUSB0", "/dev/ttyUSB1", "COM1", "COM2"])
        self.layout.addWidget(QLabel("Port:"))
        self.layout.addWidget(self.port_selector)

        self.baudrate_selector = QComboBox()
        self.baudrate_selector.addItems(["57600", "115200", "1000000"])
        self.layout.addWidget(QLabel("Baudrate:"))
        self.layout.addWidget(self.baudrate_selector)

        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.connect_to_dynamixel)
        self.layout.addWidget(self.connect_button)

        self.id_input = QLineEdit()
        self.layout.addWidget(QLabel("Dynamixel ID:"))
        self.layout.addWidget(self.id_input)

        self.torque_button = QPushButton("Torque On")
        self.torque_button.clicked.connect(self.toggle_torque)
        self.layout.addWidget(self.torque_button)

        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 4095)  # Assuming 0-4095 position range
        self.position_slider.valueChanged.connect(self.write_position)
        self.layout.addWidget(QLabel("Position:"))
        self.layout.addWidget(self.position_slider)

        self.position_label = QLabel("Current Position: ")
        self.layout.addWidget(self.position_label)

        self.read_button = QPushButton("Read Position")
        self.read_button.clicked.connect(self.read_position)
        self.layout.addWidget(self.read_button)

        self.portHandler = None
        self.packetHandler = None
        self.is_torque_on = False

    def connect_to_dynamixel(self):
        try:
            port = self.port_selector.currentText()
            baudrate = int(self.baudrate_selector.currentText())

            self.portHandler = PortHandler(port)
            self.packetHandler = PacketHandler(2.0)

            if not self.portHandler.openPort():
                raise Exception("Failed to open the port")

            if not self.portHandler.setBaudRate(baudrate):
                raise Exception("Failed to change the baudrate")

            self.show_message("Success", "Dynamixel has been successfully connected")
        except Exception as e:
            self.show_error("Connection Error", str(e))

    def toggle_torque(self):
        if self.portHandler is None or self.packetHandler is None:
            self.show_error("Error", "Please connect to Dynamixel first")
            return

        try:
            dxl_id = int(self.id_input.text())
            address = 64  # Address for Torque Enable in Dynamixel Protocol 2.0
            
            if self.is_torque_on:
                dxl_comm_result, dxl_error = self.packetHandler.write1ByteTxRx(self.portHandler, dxl_id, address, 0)
                self.is_torque_on = False
                self.torque_button.setText("Torque On")
            else:
                dxl_comm_result, dxl_error = self.packetHandler.write1ByteTxRx(self.portHandler, dxl_id, address, 1)
                self.is_torque_on = True
                self.torque_button.setText("Torque Off")

            if dxl_comm_result != COMM_SUCCESS:
                raise Exception(self.packetHandler.getTxRxResult(dxl_comm_result))
            elif dxl_error != 0:
                raise Exception(self.packetHandler.getRxPacketError(dxl_error))

            self.show_message("Success", f"Torque {'enabled' if self.is_torque_on else 'disabled'}")
        except Exception as e:
            self.show_error("Torque Control Error", str(e))

    def write_position(self):
        if self.portHandler is None or self.packetHandler is None:
            self.show_error("Error", "Please connect to Dynamixel first")
            return

        if not self.is_torque_on:
            self.show_error("Error", "Please enable torque first")
            return

        try:
            dxl_id = int(self.id_input.text())
            address = 116  # Address for Goal Position in Dynamixel Protocol 2.0
            position = self.position_slider.value()

            dxl_comm_result, dxl_error = self.packetHandler.write4ByteTxRx(self.portHandler, dxl_id, address, position)

            if dxl_comm_result != COMM_SUCCESS:
                raise Exception(self.packetHandler.getTxRxResult(dxl_comm_result))
            elif dxl_error != 0:
                raise Exception(self.packetHandler.getRxPacketError(dxl_error))

            self.position_label.setText(f"Current Position: {position}")
        except Exception as e:
            self.show_error("Write Position Error", str(e))

    def read_position(self):
        if self.portHandler is None or self.packetHandler is None:
            self.show_error("Error", "Please connect to Dynamixel first")
            return

        try:
            dxl_id = int(self.id_input.text())
            address = 132  # Address for Present Position in Dynamixel Protocol 2.0

            position, dxl_comm_result, dxl_error = self.packetHandler.read4ByteTxRx(self.portHandler, dxl_id, address)

            if dxl_comm_result != COMM_SUCCESS:
                raise Exception(self.packetHandler.getTxRxResult(dxl_comm_result))
            elif dxl_error != 0:
                raise Exception(self.packetHandler.getRxPacketError(dxl_error))

            self.position_label.setText(f"Current Position: {position}")
            self.position_slider.setValue(position)
        except Exception as e:
            self.show_error("Read Position Error", str(e))

    def show_message(self, title, message):
        QMessageBox.information(self, title, message)

    def show_error(self, title, message):
        QMessageBox.critical(self, title, message)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    wizard = DynamixelWizard()
    wizard.show()
    sys.exit(app.exec_())