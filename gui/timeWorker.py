import time

from PyQt6.QtCore import QObject, pyqtSignal


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
            if self.i == 1 or self.i % 30 == 0:
                self.signals.progress.emit()
                self.signals.time_signal.emit(time.ctime().split()[3])
