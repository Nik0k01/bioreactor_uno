import time

from PyQt6.QtCore import QObject, pyqtSignal


class WorkerSignals(QObject):
    progress = pyqtSignal()
    ph_signal = pyqtSignal()
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
            # Signal for lcd display
            self.signals.progress.emit()
            if self.i % 5 == 0:
                self.signals.ph_signal.emit()
            if self.i % 30 == 0:
                # Signal for ph_check and data writer
                self.signals.time_signal.emit(time.ctime().split()[3])
