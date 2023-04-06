import re
import serial
import serial.tools.list_ports
from PyQt6 import QtCore
from PyQt6.QtSerialPort import QSerialPort, QSerialPortInfo
import time, math


class Arduino(QtCore.QObject):
    def __init__(self):
        super(Arduino, self).__init__()
        self.ports = [port.device for port in serial.tools.list_ports.comports() if 'Arduino' in port.description]
        if not self.ports:
            self.board = None
        self.board = serial.Serial(self.ports[0], 115200, writeTimeout=0)

    @QtCore.pyqtSlot(int, int)
    def pump_speed(self, pump_number, feed):
        """
        Sets the state of a pump used for pumping nutrition or controlling the pH in the bioreactor
        :param pump_number: what kind of pump connected to arduino 0 - nutrition, 1 - acid, 2 - base
        :param feed: volume flow rate ml/min
        :return: None,
        """
        # 85 ml/min - 255, pump starts pumping anything at all from 150
        pwm_speed = 0 if feed == 0 else math.floor(feed / 85 * 75) + 150
        serial_line = f'CMD,SET_PUMP,{pump_number},{pwm_speed}\n'
        self.board.write(serial_line.encode())
        time.sleep(.1)
        self.board.reset_input_buffer()
        print('Pump has been activated!')

    def get_data(self):
        """
        Read data from the serial monitor
        :return: values of temperature, pH and saturation in oxygen
        """
        try:
            data = self.board.readline().decode().rstrip()
            # print(data)
            # print('Deciphering data...')
            time.sleep(0.1)
            return self.decipher_data(data)
        except:
            return {}

    def decipher_data(self, a_string):
        pattern = r'(\w+:\d+\.\d+)'
        numbers = re.findall(pattern, a_string)
        return {item.split(':')[0]: float(item.split(':')[1]) for item in numbers}
