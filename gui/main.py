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
    finished = pyqtSignal()
    close = pyqtSignal()


class Worker(QRunnable):

    signals = WorkerSignals()
    i = 0

    def __init__(self):
        super(Worker, self).__init__()
        self.__isRunning = True

    @pyqtSlot()
    def run(self):
        while self.__isRunning:
            self.i += 1
            time.sleep(1)
            if self.i == 1 or self.i % 5 == 0:
                self.signals.progress.emit()

    def stop(self):
        self.__isRunning = False







class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.board = self.setup_board()
        self.threadpool = QThreadPool()
        self.ui.startBtn.clicked.connect(self.timer_thread)
        self.ui.closeEvent = self.closeEvent

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

    def get_data(self):
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

    def update_lcds(self, data):
        self.ui.pHLcd.display(float(data.get('pH', -999)))
        self.ui.tempLcd.display(float(data.get('temp', -999)))
        self.ui.oxyLcd.display(float(data.get('oxy', -999)))

    def timer_thread(self):
        self.time_worker = Worker()
        self.time_worker.signals.progress.connect(lambda: self.update_lcds(self.get_data()))
        self.threadpool.start(self.time_worker)

    def closeEvent(self, event):
        msg = WorkerSignals()
        msg.close.connect(self.time_worker.stop)
        print('sending signal')
        msg.emit()
        print('sleeping')
        time.sleep(5)
        self.close()





def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
