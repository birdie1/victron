import logging
import lib.helper as helper

from vedirect import Vedirect
from lib.mappings import PID, WARN_AR, MODE, CS

logger = logging.getLogger()

# Sample data: {'AC_OUT_I': '-3', 'V': '13232', 'AR': '0', 'WARN': '0', 'PID': '0xA261', 'FW': '0114',
# 'SER#': 'HQ1936HGQYH', 'MODE': '2', 'CS': '9', 'AC_OUT_V': '23004'}


class Phoenix:
    # MAP: KEY: (Category, Description, Unit, Factor/Mapping, Interpret_function)
    MAP = {
        'AC_OUT_I': ("Latest", "AC Current", "A", 0.1, helper.convert_int_factor),
        'AC_OUT_V': ("Latest", "AC Voltage", "V", 0.01, helper.convert_int_factor),
        'V': ("Latest", "Voltage", "V", 0.001, helper.convert_int_factor),
        'AR': ("Latest", "Alarm Reason", "", WARN_AR, helper.convert_warn_ar),
        'WARN': ("Latest", "Warning", "", WARN_AR, helper.convert_warn_ar),
        'PID': ("Meta", "Product ID", "", PID, helper.convert_map_out),
        'FW': ("Meta", "Firmware", "", 0, helper.convert_firmware),
        'SER#': ("Meta", "Serial", "", 0, helper.convert_str_out),
        'MODE': ("Latest", "Mode", "", MODE, helper.convert_map_out),
        'CS': ("Latest", "Status", "", CS, helper.convert_map_out),
        'PROD': ("Meta", "Production Date", "", 0, helper.convert_production_date),
    }

    def __init__(self, name, port):
        self.name = name
        self.port = port
        self.ve = Vedirect(self.port, 60)

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
