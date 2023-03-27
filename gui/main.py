import sys
import warnings
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import time
import serial, serial.tools.list_ports
import re
from ui_MainWindow import Ui_MainWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.board = self.setup_board()

    def setup_board(self):
        ports = [port.device for port in serial.tools.list_ports.comports() if 'Arduino' in port.description]
        if not ports:
            self.ui.portStatus.setText('Nie znaleziono urządzenia Ardunio - upewnij się, \n'
                                       'że jest podłączone lub zresetuj komputer.')
            self.ui.portStatus.adjustSize()
            return None
        if len(ports) > 1:
            self.ui.portStatus.setText('Znaleziono kilka urządzeń Arduino - użyto pierwsze znalezione urządzenie')
            self.ui.portStatus.adjustSize()
            return serial.Serial(ports[0], 115200)
        else:
            self.ui.portStatus.setText(f'{ports[0]}')
            return serial.Serial(ports[0], 115200)

    def decipher_data(self, a_string):
        numbers = re.findall(r'\d+\.\d+', a_string)
        names = ['temp', 'pH', 'oxy']
        return {name: number for name, number in zip(names, numbers)}

    def update_lcds(self, data):
        self.ui.pHLcd.display(float(data.get('pH', -999)))
        self.ui.tempLcd.display(float(data.get('temp', -999)))
        self.ui.oxyLcd.display(float(data.get('oxy', -999)))



def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
