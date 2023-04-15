import lib.helper as helper
from lib.mappings import PID, WARN_AR, CS, ERROR, OR, MPPT

# Example:
# {'PID': '0xA056', 'FW': '156', 'SER#': 'HQ2027LDKCU', 'V': '13330', 'I': '5800', 'VPV': '81010',
# 'PPV': '80', 'CS': '3', 'MPPT': '2', 'OR': '0x00000000', 'ERR': '0', 'LOAD': 'ON', 'H19': '26518', 'H20': '8',
# 'H21': '79', 'H22': '67', 'H23': '267', 'HSDS': '358'}

value_description_map = {
    'V': ("Latest", "Voltage", "V", 0.001, helper.convert_int_factor),
    'I': ("Latest", "Current", "A", 0.001, helper.convert_int_factor),
    'IL': ("Latest", "Load Current", "A", 0.001, helper.convert_int_factor),
    'VPV': ("Latest", "Voltage Panel", "V", 0.001, helper.convert_int_factor),
    'PPV': ("Latest", "Power", "W", 1, helper.convert_int_factor),
    'CS': ("Latest", "Status", "", CS, helper.convert_map_out),
    'MPPT': ("Latest", "MPPT Tracker Operation Mode", "", MPPT, helper.convert_map_out),
    'OR': ("Latest", "Off Reason", "", OR, helper.convert_map_out),
    'ERR': ("Latest", "Error Code", "", ERROR, helper.convert_map_out),
    'LOAD': ("Latest", "Virtual Load Output", "", 0, helper.convert_str_out),
    'H19': ("History", "Energy All Time", "kWh", 0.01, helper.convert_int_factor),
    'H20': ("History", "Energy Today", "kWh", 0.01, helper.convert_int_factor),
    'H21': ("History", "Max Power Today", "W", 1, helper.convert_int_factor),
    'H22': ("History", "Energy Yesterday", "kWh", 0.01, helper.convert_int_factor),
    'H23': ("History", "Max Power Yesterday", "W", 1, helper.convert_int_factor),
    'HSDS': ("Meta", "Day sequence Number (0..364)", "", 1, helper.convert_int_factor),
    'PID': ("Meta", "Product ID", "", PID, helper.convert_map_out),
    'FW': ("Meta", "Firmware Version", "", "", helper.convert_firmware),
    'SER#': ("Meta", "Serial", "", 0, helper.convert_str_out),
    'PROD': ("Meta", "Production Date", "", 0, helper.convert_production_date),
}
