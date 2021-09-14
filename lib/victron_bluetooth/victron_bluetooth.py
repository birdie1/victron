import copy
import gatt
import logging
import time
import lib.helper
from collections import namedtuple
from enum import IntEnum

logger = logging.getLogger()
manager = gatt.DeviceManager(adapter_name="hci0")

VALUE_PREFIX = bytes.fromhex("08031903")
Header = namedtuple("Header", ["value_type", "category_type", "length"])
COMMAND_POS = 0
LENGHT_TYPE_POS = 1
DATA_POS = 2
HISTORY_MIN_CMD = 0x50
HISTORY_MAX_CMD = HISTORY_MIN_CMD + 31


class VALUE_TYPES(IntEnum):
    FIXED_LEN = 0x09
    VAR_LEN = 0x08


TYPE_NAMES = {
    0x1: "unknown",
    0x2: "unknown",
    0x4: "single value reply",
    0x8: "unknown",
}

FIXED_DATA_NAMES = {
    0x7D: ("FIXED Starter", 100, "V"),
    0x8C: ("FIXED Current", 1000, "A"),
    0x8D: ("FIXED Voltage", 100, "V"),
    0x8E: ("FIXED Power", 1, "W"),
    0x8F: ("FIXED Capacity", 100, "%"),
}

MIXED_SETTINGS_NAMES = {
    0xFE: ("Battery", "Time to go", "min", 1, False, lib.helper.convert_value_int),
    0xFF: ("Battery", "Charge Status", "%", 100, False, lib.helper.convert_value_number),
}

HISTORY_VALUE_NAMES = {
    0x00: ("History", "Deepest Discharge", "Ah", 10, True, lib.helper.convert_value_number),
    0x01: ("History", "Last Discharge", "Ah", 10, True, lib.helper.convert_value_number),
    0x02: ("History", "Average Discharge", "Ah", 10, True, lib.helper.convert_value_number),
    0x03: ("History", "Total Charge Cycles", "", 1, False, lib.helper.convert_value_number),
    0x04: ("History", "Full Discharges", "", 1, False, lib.helper.convert_value_number),
    0x05: ("History", "Cumulative Ah Drawn", "Ah", 10, True, lib.helper.convert_value_number),
    0x06: ("History", "Min Battery Voltage", "V", 100, False, lib.helper.convert_value_number),
    0x07: ("History", "Max Battery Voltage", "V", 100, False, lib.helper.convert_value_number),
    0x08: ("History", "Time Since Last Full", "sec", 1, True, lib.helper.convert_value_int),
    0x09: ("History", "Synchronizations", "", 1, False, lib.helper.convert_value_number),
    0x0A: ("History", "Number of Low Voltage Alarms", "", 1, False, lib.helper.convert_value_number),
    0x0B: ("History", "Number of High Voltage Alarms", "", 1, False, lib.helper.convert_value_number),
    0x0E: ("History", "Minimum Starter Voltage (1)", "", 100, False, lib.helper.convert_value_number),
    0x0F: ("History", "Maximum Starter Voltage (1)", "", 100, False, lib.helper.convert_value_number),
    0x10: ("History", "Discharged Energy", "Ah", 100, False, lib.helper.convert_value_number),
    0x11: ("History", "Charged Energy", "Ah", 100, False, lib.helper.convert_value_number),
}

SETTINGS_AND_SOLAR_HISTORY_VALUE_NAMES = {
    0x00: ("Settings", "Capacity", "Ah", 1, False, lib.helper.convert_value_number),
    0x01: ("Settings", "Charged Voltage", "V", 1, False, lib.helper.convert_value_number),
    0x02: ("Settings", "Tail Current", "A", 1, False, lib.helper.convert_value_number),
    0x03: ("Settings", "Charged Detection Time", "sec", 1, False, lib.helper.convert_value_number),
    0x04: ("Settings", "Charge effectic factor", "", 1, False, lib.helper.convert_value_number),
    0x05: ("Settings", "Peukert Coefficient", "", 1, False, lib.helper.convert_value_number),
    0x06: ("Settings", "Current Threshold", "%", 1, False, lib.helper.convert_value_number),
    0x07: ("Settings", "Time-to-go avg. per.", "sec", 1, False, lib.helper.convert_value_number),
    0x08: ("Settings", "Discharge Floor", "%", 1, False, lib.helper.convert_value_number),
    0x09: ("Settings", "Relay Low Soc Clear", "%", 1, False, lib.helper.convert_value_number),
    0x34: ("Settings", "User Current Zero (read only)", "", 1, False, lib.helper.convert_value_number),
}


VALUE_VALUE_NAMES = {
    0x8C: ("Latest", "Current", "A", 1000, True, lib.helper.convert_value_number),
    0x8D: ("Latest", "Voltage", "V", 100, False, lib.helper.convert_value_number),
    0x8E: ("Latest", "Power", "W", 1.0, True, lib.helper.convert_value_number),
    0x7D: ("Latest", "Starter", "V", 100, True, lib.helper.convert_value_number),
    0x8F: ("Latest", "SmartSolar Battery Current", "A", 10, True, lib.helper.convert_value_number),
    0xBC: ("Latest", "SmartSolar Power", "W", 100, True, lib.helper.convert_value_number),
    0xBD: ("Latest", "SmartSolar Solar Current", "A", 10, True, lib.helper.convert_value_number),
    0xBB: ("Latest", "SmartSolar Solar Voltage", "V", 100, True, lib.helper.convert_value_number),
    0xEF: ("Latest", "SmartSolar Setting Battery Voltage", "V", 1, True, lib.helper.convert_value_number),
    0xF0: ("Latest", "SmartSolar Setting Charge Current", "A", 1, True, lib.helper.convert_value_number),
    0xF6: ("Latest", "SmartSolar Setting Float Voltage", "V", 100, True, lib.helper.convert_value_number),
}

ORION_SETTINGS_NAMES = {
    0x36: ("Settings", "Shutdown Voltage", "V", 100, True, lib.helper.convert_value_number),
    0x37: ("Settings", "Start Voltage", "V", 100, True, lib.helper.convert_value_number),
    0x38: ("Settings", "Delayed Start Voltage", "V", 100, True, lib.helper.convert_value_number),
    0x39: ("Settings", "Orion Start Delay", "sec", 1, True, lib.helper.convert_value_number),
}

ORION_VALUE_NAMES = {
    0xBB: ("Latest", "Input Voltage", "V", 100, True, lib.helper.convert_value_number),
    0xE9: ("Settings", "Delayed start voltage delay", "sec", 10, True, lib.helper.convert_value_number),
}

## Found in PDF: VE.Can registers
PRODUCT_INFO_NAMES = {
    0x00: ("Product", "ID", "", 1, True, lib.helper.convert_value_unknown),
    0x01: ("Product", "Revision", "", 1, True, lib.helper.convert_value_unknown),
    0x02: ("Product", "Firmware Version", "", 1, True, lib.helper.convert_value_firmware),
    0x03: ("Product", "Minimum Firmware Version", "", 1, True, lib.helper.convert_value_unknown),
    0x04: ("Product", "GroupID", "", 1, True, lib.helper.convert_value_unknown),
    0x05: ("Product", "Hardware Revision", "", 1, True, lib.helper.convert_value_unknown),
    0x0A: ("Product", "Serial", "", 1, True, lib.helper.convert_value_string),
    0x0B: ("Product", "Model Name", "", 1, True, lib.helper.convert_value_unknown),
    0x0C: ("Product", "Installation description 1", "", 1, True, lib.helper.convert_value_unknown),
    0x0D: ("Product", "Installation description 2", "", 1, True, lib.helper.convert_value_unknown),
    0x0E: ("Product", "Identify", "", 1, True, lib.helper.convert_value_identify),
    0x10: ("Product", "Udf version", "", 1, True, lib.helper.convert_value_udf),
    0x20: ("Product", "Uptime", "", 1, True, lib.helper.convert_value_unknown),
    0x40: ("Product", "Capabilities (NOT DECODED, See PDF Ve.Direct Protocol)", "", 1, True, lib.helper.convert_value_unknown),
}

# Category lookup
# Description: Lookup base command
#       0x01190308 -> 0x01 you will find in the description pdfs from victron for other buses, like ve.direct or ve.can
#
# HEX VALUE -> (Description, value array, converter)
# 0x??: ("Battery", "Time to go", "min", 1, False),
VARLEN_CATEGORY_LOOKUP = {
    0x01190308: ("Product Info", PRODUCT_INFO_NAMES),
    0x03190308: ("history values", HISTORY_VALUE_NAMES),
    0x10190308: ("settings valu", SETTINGS_AND_SOLAR_HISTORY_VALUE_NAMES),
    0xED190308: ("values values", VALUE_VALUE_NAMES),
    0x0F190308: ("mixed settings", MIXED_SETTINGS_NAMES),
    0x01190008: ("Orion Values UKNNOWN", ORION_VALUE_NAMES),
    0xEC190008: ("streaming smartshunt UNKKNOWN", VALUE_VALUE_NAMES),
    0xED190008: ("Orion Values", ORION_VALUE_NAMES),
    0xEE190008: ("Orion Settings", ORION_SETTINGS_NAMES),
}

FIXEDLEN_CATEGORY_LOOKUP = {
    0x03190308: ("history values", HISTORY_VALUE_NAMES, None),
    0x03190309: "history bools",
    0x10190308: "settings values",
    0x10190309: "settings bools",
    0xED190308: ("values values", FIXED_DATA_NAMES, None),
    0xED190309: "values bools",
    0x0F190308: "mixed settings",
}

SIGNATURE = [
    (1, (0x03, 0x00)),
    (2, (0x19,)),
]

SOLAR_HISTORY_VALUES = [
    (12, 2, ("History", "Battery Voltage Max", "V", 100, True)),
    (14, 2, ("History", "Battery Voltage Min", "V", 100, True)),
    (21, 2, ("History", "Total Work", "kWh", 100, False)),
    (27, 1, ("History", "Solar Power Max", "W", 1, False)),
    (33, 2, ("History", "Solar Voltage Max", "V", 100, True)),
    # array always is 36bytes
]


class VictronBluetooth:
    def __init__(self, device_config):
        self.device_config = device_config
        self.victron_device = None
        self.gatt_device = None
        self.output = None
        self.buffer = bytearray()

        if self.device_config['type'] == 'smartsolar':
            from lib.victron_bluetooth.victron_smartsolar import Smartsolar
            self.victron_device = Smartsolar(self.device_config)
        if self.device_config['type'] == 'smartshunt':
            from lib.victron_bluetooth.victron_smartshunt import Smartshunt
            self.victron_device = Smartshunt(self.device_config)

    def get_device_info(self):
        pass

    def get_mapping_table(self):
        pass

    def finished_target(self):
        self.gatt_device.disconnect()
        logger.debug(f'{self.device_config["name"]}: Thread finished')
        manager.stop()

    def read(self, output):
        self.output = output

        self.gatt_device = self.victron_device.get_gatt_device_instance(
            manager,
            self.handle_single_value,
            self.handle_bulk_values,
            self.finished_target
        )

        manager.start_discovery()
        time.sleep(2)

        # TODO: Stuff like reconnecting after time
        try:
            logger.info(f'{self.device_config["name"]}: Connecting...')
            self.gatt_device.connect()
        except:
            logger.error(f"{self.device_config['name']}: failed to connect. Trying again shortly.")

        manager.stop_discovery()
        manager.run()



    def handle_bulk_values(self, value):
        self.buffer.extend(value)

        pos = self.start_of_packet(self.buffer)
        while len(self.buffer) > 0 and pos >= 0:
            consumed = self.handle_one_value(self.buffer[pos:])
            if consumed == -1:
                logger.debug(f'UNRECOGNIZED DATA: {self.device_config["name"]}: bulk: need more bytes')
                return
            buffer = self.buffer[pos + consumed:]
            pos = self.start_of_packet(self.buffer)
            if pos > 0:  # TODO BUG: midnight hacking
                unknown = buffer[:pos]
                logger.debug(f'UNRECOGNIZED DATA: {self.device_config["name"]}: unknown value in bulk: {unknown}')

    def handle_single_value(self, value):
        value_origin = copy.deepcopy(value)
        pos = self.start_of_packet(value)
        while pos >= 0:
            consumed = self.handle_one_value(value[pos:])
            value = value[pos + consumed :]
            pos = self.start_of_packet(value)
        if len(value) > 0:
            logger.debug(f'UNRECOGNIZED DATA: {self.device_config["name"]}: unknown single packet: value:{value} - value_origin:{value_origin}')

    def decode_history_packet(self, command, value):
        total_length = value[DATA_POS]
        if len(value) < total_length:
            return "", -1

        values = []
        for config in SOLAR_HISTORY_VALUES:
            command = config[2]
            data = value[config[0] : config[0] + config[1]]
            values += [{"command": command, "value": lib.helper.convert_value_number(data, command)}]

        day_index = value[35]
        logger.debug(f"Day Index: {day_index -54} alternative (should match): {command-0x50}")
        return values, total_length

    def decode_var_len(self, value, config_table):
        length_type_field = value[LENGHT_TYPE_POS]
        length = length_type_field & 0x0F
        type_id = (length_type_field & 0xF0) >> 4
        data = value[DATA_POS:DATA_POS + length]

        command = value[COMMAND_POS]
        if HISTORY_MIN_CMD <= command <= HISTORY_MAX_CMD:
            return self.decode_history_packet(command, value)

        if command not in config_table:
            raise KeyError(f"unknown command (in var len) 0x{command:x} in {config_table.keys()}")

        #data_label = get_label(command, config_table)
        #config = config_table[command]
        #data_string = format_value(data, config)
        command = self.get_command(command, config_table)
        value_string = command[5](data, command)

        consumed = 2 + length
        return [{"command": command, "value": value_string}], consumed

    def decode_fixed_len(self, value):
        """function expects whole packet with 4-byte prefix"""
        DATATYPE_POS = 0
        DATA_POS = 1
        consumed = 2

        data = value[DATA_POS]
        data_type = value[DATATYPE_POS]
        command = self.get_command(data_type, MIXED_SETTINGS_NAMES)
        if not command:
            raise KeyError(f"unknown command (in fixed len) 0x{command:x}")
        value_string = lib.helper.convert_value_number(data, command)

        return [{"command": command, "value": value_string}], consumed

    def start_of_packet(self, value):
        for offset, _ in enumerate(value):
            # slice from start of signature to end
            result = self.signature_complete(value[offset:], SIGNATURE)
            if result:
                return offset
        return -1

    def get_command(self, command, command_names):
        try:
            return command_names[command]
        except:
            return False

    def decode_header(self, header_4b):
        return Header(VALUE_TYPES(header_4b[0]), int.from_bytes(bytes(header_4b[:4]), "little"), 4)

    def signature_complete(self, value, signature):
        try:
            for pos, sigs in signature:
                if not value[pos] in sigs:
                    return False
            return True
        except:
            return False

    def handle_one_value(self, value):
        header = self.decode_header(value)

        if (
            header.value_type == VALUE_TYPES.FIXED_LEN
            and len(value) < 6
            or header.value_type == VALUE_TYPES.VAR_LEN
            and len(value) < 6
        ):
            return -1

        result = ""
        consumed = header.length
        used = 0

        if header.value_type == VALUE_TYPES.FIXED_LEN:
            result, used = self.decode_fixed_len(value[consumed:])
            #if not command:
            #    logger.warning(f'{device_name}: {value}')
            #    return consumed

        if header.value_type == VALUE_TYPES.VAR_LEN:
            category = VARLEN_CATEGORY_LOOKUP[header.category_type]
            result, used = self.decode_var_len(value[consumed:], category[1])

        for i in range(len(result)):
            value_name = result[i]['command'][1]
            value = result[i]['value']

            logger.debug(f'{self.device_config["name"]}: Collected {value_name} -> {value}')
            self.output(value_name, value)
            #else:
            #    # Set collection value and check if collection is ready
            #
            #    col_key = set_value_in_collections(device, device_name, value_name, value)
            #    if not col_key:
            #        logger.debug(f'{device_name}: {value_name} not in any collections, it will never be published')
            #    else:
            #        if collection_check_full(device.collections[col_key]):
            #            logger.info(f'Collection is full, sending data via {device.config["logger"]}')
            #            logger.debug(f'{device_name}: Collection:  {json.dumps(device.collections[col_key])}')
            #            output(device_name, col_key, device.collections[col_key])
            #
            #            device.reset_collection(col_key)
            #            if config['direct_disconnect']:
            #                disconnect_loop(device.gatt_device)

        consumed += used

        return consumed
