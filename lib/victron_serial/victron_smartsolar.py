import logging
import lib.helper as helper

from vedirect import Vedirect
from lib.mappings import PID, WARN_AR, CS, ERROR, OR, MPPT

logger = logging.getLogger()

# Example:
# {'PID': '0xA056', 'FW': '156', 'SER#': 'HQ2027LDKCU', 'V': '13330', 'I': '5800', 'VPV': '81010',
# 'PPV': '80', 'CS': '3', 'MPPT': '2', 'OR': '0x00000000', 'ERR': '0', 'LOAD': 'ON', 'H19': '26518', 'H20': '8',
# 'H21': '79', 'H22': '67', 'H23': '267', 'HSDS': '358'}


class Smartsolar:
    # MAP: KEY: (Category, Description, Unit, Factor/Mapping, Interpret_function)
    MAP = {
        'V': ("Latest", "Voltage", "V", 0.001, helper.convert_int_factor),
        'I': ("Latest", "Current", "A", 0.001, helper.convert_int_factor),
        'VPV': ("Latest", "Voltage Panel", "V", 0.001, helper.convert_int_factor),
        'PPV': ("Latest", "Power", "W", 1, helper.convert_int_factor),
        'CS': ("Latest", "Status", "", CS, helper.convert_map_out),
        'MPPT': ("Latest", "MPPT Tracker Operation Mode", "", MPPT, helper.convert_map_out),
        'OR': ("Latest", "Off Reason", "", OR, helper.convert_map_out),
        'ERR': ("Latest", "Error Code", "", ERROR, helper.convert_map_out),
        'LOAD': ("Latest", "Virtual Load Output", "", 0, helper.convert_str_out),
        'H19': ("History", "Energy All Time", "kWh", 0.01, helper.convert_int_factor),
        'H20': ("History", "Energy Today", "kWh", 0.01, helper.convert_int_factor),
        'H21': ("History", "Energy Today Max", "W", 1, helper.convert_int_factor),
        'H22': ("History", "Energy Yesterday", "kWh", 0.01, helper.convert_int_factor),
        'H23': ("History", "Energy Yesterday Max", "W", 1, helper.convert_int_factor),
        'HSDS': ("Meta", "Day sequence Number (0..364)", "", 1, helper.convert_int_factor),
        'PID': ("Meta", "Product ID", "", PID, helper.convert_map_out),
        'FW': ("Meta", "Firmware Version", "", "", helper.convert_firmware),
        'SER#': ("Meta", "Serial", "", 0, helper.convert_str_out),
        'PROD': ("Meta", "Production Date", "", 0, helper.convert_production_date),
    }

    def __init__(self, name, port):
        self.name = name
        self.port = port
        self.ve = Vedirect(self.port, 60)

    def get_mapping_table(self):
        return self.MAP

    def get_device_info(self):
        data = self.ve.read_data_single()
        pid = self.MAP['PID'][4](data['PID'], self.MAP['PID'])
        ser = self.MAP['SER#'][4](data['SER#'], self.MAP['SER#'])
        fw = self.MAP['FW'][4](data['FW'], self.MAP['FW'])
        return pid, ser, fw

    def get_data(self, output):
        for key, value in self.ve.read_data_single().items():
            if key not in self.MAP:
                logger.warning(f'{self.name}: {key} not found in mapping dictionary')
            else:
                if key == 'SER#':
                    self.send_out('PROD', value, output)

                self.send_out(key, value, output)

    def send_out(self, key, value, output):
        command = self.MAP[key]
        data = command[4](value, command)
        output(command[1], data)
