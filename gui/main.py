import sys
import warnings
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import time
import serial, serial.tools.list_ports
import re
from ui_MainWindow import Ui_MainWindow


class WorkerSignals(QObject):
    progress = pyqtSignal()
    time_signal = pyqtSignal(object)


class Worker(QObject):
    signals = WorkerSignals()
    i = 0

    def __init__(self):
        super(Worker, self).__init__()

    def run(self):
        while True:
            self.i += 1
            time.sleep(1)
            if self.i == 1 or self.i % 5 == 0:
                self.signals.progress.emit()
                self.signals.time_signal.emit(time.ctime().split()[3])


class Arduino():
    def __init__(self):
        self.ports = [port.device for port in serial.tools.list_ports.comports() if 'Arduino' in port.description]
        if not self.ports:
            self.board = None
        self.board = serial.Serial(self.ports[0], 115200)

    def pump_speed(self, pump_number, feed):
        """
        Sets the state of a pump used for pumping nutrition or controlling the pH in the bioreactor
        :param pump_number: what kind of pump connected to arduino 1 - nutrition, 2 - acid, 3 - base
        :param feed: volume flow rate ml/min
        :return: None,
        """
        # 85 ml/min - 255, pump starts pumping anything at all from 120
        pwm_speed = 0 if feed == 0 else feed / 85 * 135 + 120
        serial_line = f'CMD,SET_PUMP,{pump_number},{pwm_speed}'
        self.board.write(serial_line.encode())

    def get_data(self):
        """
        Read data from the serial monitor
        :return: values of temperature, pH and saturation in oxygen
        """
        try:
            print('Getting data...')
            data = self.board.readline().decode().rstrip()
            print('Deciphering data...')
            return self.decipher_data(data)
        except:
            return {}

    def decipher_data(self, a_string):
        numbers = re.findall(r'\d+\.\d+', a_string)
        names = ['temp', 'pH', 'oxy']
        return {name: number for name, number in zip(names, numbers)}


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.board = Arduino()
        self.threadpool = QThreadPool()
        self.dataFile = open(f'data_log/data{time.ctime().replace(" ", "_").replace(":", "_")}.txt', 'w')
        self.ui.nutriSlider.valueChanged.connect(lambda: self.ui.nutriLcd.display(self.ui.nutriSlider.value()))


        # Permanent thread for timing measurements
        self.time_worker = Worker()
        self.time_thread = QThread()
        self.time_worker.moveToThread(self.time_thread)
        self.time_worker.signals.progress.connect(lambda: self.update_lcds(self.board.get_data()))
        self.time_worker.signals.time_signal.connect(self.data_writer)
        self.time_thread.started.connect(self.time_worker.run)
        self.ui.startBtn.clicked.connect(self.time_thread.start)

    def board_info(self):
        """
        Inform a user about the status of arduino board
        """
        if not self.board.ports:
            self.ui.portStatus.setText('Nie znaleziono urządzenia Arduino - upewnij się, \n'
                                       'że jest podłączone lub zresetuj komputer.')
            self.ui.portStatus.adjustSize()
        if len(self.board.ports) > 1:
            self.ui.portStatus.setText('Znaleziono kilka urządzeń Arduino - użyto pierwsze znalezione urządzenie')
            self.ui.portStatus.adjustSize()
        else:
            self.ui.portStatus.setText(f'{self.board.ports[0]}')

    def update_lcds(self, data):
        self.ui.pHLcd.display(float(data.get('pH', -999)))
        self.ui.tempLcd.display(float(data.get('temp', -999)))
        self.ui.oxyLcd.display(float(data.get('oxy', -999)))

    @pyqtSlot(object)
    def data_writer(self, time_signal):
        data_line = f'{time_signal} : Temp = {self.ui.tempLcd.value()} *C : ' \
                    f'pH = {self.ui.pHLcd.value()} : Oxygen = {self.ui.oxyLcd.value()} mg/L :' \
                    f' Q_in = {self.ui.nutriLcd.value()} ml/min \n'
        print(data_line)
        self.dataFile.write(data_line)
        self.dataFile.flush()

    def closeEvent(self, event):

        reply = QMessageBox.question(self, 'Message',
                    "Are you sure to quit?", QMessageBox.StandardButton.Yes |
                    QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.dataFile.close()
            self.time_thread.quit()
            event.accept()
        else:
            event.ignore()





def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
