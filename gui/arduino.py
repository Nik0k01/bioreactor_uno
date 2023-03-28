import re
import serial
import serial.tools.list_ports


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
        self.board.write(serial_line.encode('UTF-8'))

    def get_data(self):
        """
        Read data from the serial monitor
        :return: values of temperature, pH and saturation in oxygen
        """
        try:
            self.board.write('DEBUG_PUMP,1'.encode('UTF-8'))
            data = self.board.readline().decode().rstrip()
            print(data)
            print('Deciphering data...')
            return self.decipher_data(data)
        except:
            return {}

    def decipher_data(self, a_string):
        numbers = re.findall(r'\d+\.\d+', a_string)
        names = ['temp', 'pH', 'oxy']
        return {name: number for name, number in zip(names, numbers)}
