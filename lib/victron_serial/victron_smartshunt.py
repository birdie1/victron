import logging
import lib.helper as helper

from vedirect import Vedirect
from lib.mappings import PID, WARN_AR

logger = logging.getLogger()

# Example: {'H1': '-264148', 'H2': '-2909', 'H3': '-109417', 'H4': '6', 'H5': '1', 'H6': '-3928992', 'H7': '6200',
# 'H8': '14592', 'H9': '3331', 'H10': '21', 'H11': '0', 'H12': '0', 'H15': '-27', 'H16': '14592', 'H17': '5148',
# 'H18': '5581', 'PID': '0xA389', 'V': '13259', 'VS': '12716', 'I': '-7742', 'P': '-103', 'CE': '-2911', 'SOC': '990',
# 'TTG': '2052', 'Alarm': 'OFF', 'AR': '0', 'BMV': 'SmartShunt 500A/50mV', 'FW': '0407', 'MON': '0'}
#


class Smartshunt:
    # MAP: KEY: (Category, Description, Unit, Factor/Mapping, Interpret_function)
    MAP = {
        'H1': ("History", "Deepest Discharge", "Ah", 0.001, helper.convert_int_factor),
        'H2': ("History", "Last Discharge", "Ah", 0.001, helper.convert_int_factor),
        'H3': ("History", "Average Discharge", "Ah", 0.001, helper.convert_int_factor),
        'H4': ("History", "Charge Cycles", "", 1, helper.convert_int_factor),
        'H5': ("History", "Full Discharges", "", 1, helper.convert_int_factor),
        'H6': ("History", "Cumulative Ah Drawn", "Ah", 0.001, helper.convert_int_factor),
        'H7': ("History", "Battery Voltage min", "V", 0.001, helper.convert_int_factor),
        'H8': ("History", "Battery Voltage max", "V", 0.001, helper.convert_int_factor),
        'H9': ("History", "Time Since Last Full", "s", 1, helper.convert_int_factor),
        'H10': ("History", "Synchonisations", "", 1, helper.convert_int_factor),
        'H11': ("History", "Alarm Voltage low", "", 1, helper.convert_int_factor),
        'H12': ("History", "Alarm Voltage high", "", 1, helper.convert_int_factor),
        'H15': ("History", "Starter Battery Voltage min", "V", 0.001, helper.convert_int_factor),
        'H16': ("History", "Starter Battery Voltage max", "V", 0.001, helper.convert_int_factor),
        'H17': ("History", "Total Discharged Energy", "kWh", 0.01, helper.convert_int_factor),
        'H18': ("History", "Total Charged Energy", "kWh", 0.01, helper.convert_int_factor),
        'PID': ("Meta", "Product ID", "", PID, helper.convert_map_out),
        'V': ("Latest", "Voltage", "V", 0.001, helper.convert_int_factor),
        'VS': ("Latest", "Starter Battery Voltage", "V", 0.001, helper.convert_int_factor),
        'I': ("Latest", "Current", "A", 0.001, helper.convert_int_factor),
        'P': ("Latest", "Power", "W", 1, helper.convert_int_factor),
        'T': ("Latest", "Battery Temperature", "°C", 1, helper.convert_int_factor),
        'CE': ("Latest", "Used Energy", "Ah", 0.001, helper.convert_int_factor),
        'SOC': ("Battery", "State Of Charge", "%", 0.1, helper.convert_int_factor),
        'TTG': ("Battery", "Time To Go", "Min", 1, helper.convert_int_factor),
        'Alarm': ("Latest", "Alarm", "", 0, helper.convert_str_out),
        'AR': ("Latest", "Alarm Reason", "", WARN_AR, helper.convert_warn_ar),
        'BMV': ("Meta", "BMV", "", "", helper.convert_str_out),
        'FW': ("Meta", "Firmware Version", "", "", helper.convert_firmware),
        'MON': ("Meta", "MON ?", "", "", helper.convert_str_out),
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
                command = self.MAP[key]
                data = command[4](value, command)
                output(command[1], data)
