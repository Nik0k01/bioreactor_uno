import time

from PyQt6.QtCore import QObject, pyqtSignal, QRunnable, pyqtSlot


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
            self.signals.pump_run.emit(1, 85)
            # Pump base for 8 seconds
            time.sleep(8)
            self.signals.pump_run.emit(1, 0)
        # If the pH is to high turn acid pumpp
        else:
            self.signals.pump_run.emit(2, 85)
            # Pump acid for 8 seconds
            time.sleep(8)
            self.signals.pump_run.emit(2, 0)
        time.sleep(15)
        print('Done pumping')
