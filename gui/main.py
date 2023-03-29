import sys
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
import time

from gui.arduino import Arduino
from gui.timeWorker import Worker
from ui_MainWindow import Ui_MainWindow


class SignalPh(QObject):
    pump_run = pyqtSignal(int, int)


class WorkerPh(QRunnable):

    def __init__(self, ph_goal, ph_current):
        super(WorkerPh, self).__init__()
        self.ph_goal = ph_goal
        self.signals = SignalPh()
        self.ph_current = ph_current

    @pyqtSlot(float)
    def run(self):
        # If the pH is to low turn base pump
        if self.ph_goal - self.ph_current > 0:
            self.signals.pump_run.emit(2, 85)
            # Pump base for 8 seconds
            time.sleep(8)
            self.signals.pump_run.emit(2, 0)
        # If the pH is to high turn acid pumpp
        else:
            self.signals.pump_run.emit(3, 255)
            # Pump acid for 8 seconds
            time.sleep(8)
            self.signals.pump_run.emit(3, 0)
        print('Done pumping')




class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.board = Arduino()
        self.board_info()
        self.threadpool = QThreadPool()
        self.dataFile = open(f'data_log/data{time.ctime().replace(" ", "_").replace(":", "_")}.txt', 'w')
        self.ui.nutriSlider.valueChanged.connect(lambda: self.ui.nutriLcd.display(self.ui.nutriSlider.value()))
        self.ui.nutriSlider.valueChanged.connect(lambda: self.board.pump_speed(1, self.ui.nutriSlider.value()))


        # Permanent thread for timing measurements
        self.time_worker = Worker()
        self.time_thread = QThread()
        self.time_worker.moveToThread(self.time_thread)
        self.time_worker.signals.progress.connect(lambda: self.update_lcds(self.board.get_data()))
        self.time_worker.signals.progress.connect(lambda: self.ph_check())
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

    def ph_check(self):
        # Check if the pH is allright and prevent running multiple threads of running this task (pH adjustment takes
        # some time)
        if self.threadpool.activeThreadCount() < 3 and abs(self.ui.pHLcd.value() - self.ui.phSetBox.value()) > 0.3:
            ph_worker = WorkerPh(self.ui.phSetBox.value(), self.ui.pHLcd.value())
            ph_worker.signals.pump_run.connect(self.board.pump_speed)
            self.threadpool.start(ph_worker)


    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message',
                    "Czy na pewno chcesz wyjść?", QMessageBox.StandardButton.Yes |
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
