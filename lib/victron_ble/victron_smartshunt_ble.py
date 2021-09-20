import logging
from lib.victron_ble.victron_gatt_ble import AnyDevice, gatt_device_instance
import lib.helper
logger = logging.getLogger()


class SmartshuntBLE:
    # +--------------------------------------+-------------------------+-------------+------+-------+---------+---------------------------------+
    # | UUID                                 | Characteristic          | Access      | Type | Scale | Unit    | Special values                  |
    # +--------------------------------------+-------------------------+-------------+------+-------+---------+------------+--------------------+
    # | 6597ffff-4bda-4c1e-af4b-551c4cf74769 | Keep-alive              | Write/Read  | un16 | 0,001 | Seconds | 0xFFFF     | keep-alive forever |
    # +--------------------------------------+-------------------------+-------------+------+-------+---------+------------+--------------------+
    # | 6597eeff-4bda-4c1e-af4b-551c4cf74769 | Consumed Ah             | Read/Notify | sn32 | 0,1   | Ah      |            |                    |
    # +--------------------------------------+-------------------------+-------------+------+-------+---------+------------+--------------------+
    # | 6597ed8e-4bda-4c1e-af4b-551c4cf74769 | Power                   | Read/Notify | sn16 | 1     | W       | 0x7FFF     | not available      |
    # +--------------------------------------+-------------------------+-------------+------+-------+---------+------------+--------------------+
    # | 6597ed8d-4bda-4c1e-af4b-551c4cf74769 | Voltage                 | Read/Notify | sn16 | 0,01  | V       | 0x7FFF     | not available      |
    # +--------------------------------------+-------------------------+-------------+------+-------+---------+------------+--------------------+
    # | 6597ed8c-4bda-4c1e-af4b-551c4cf74769 | Current                 | Read/Notify | sn32 | 0,001 | A       | 0x7FFFFFFF | not available      |
    # +--------------------------------------+-------------------------+-------------+------+-------+---------+------------+--------------------+
    # | 65970fff-4bda-4c1e-af4b-551c4cf74769 | State of charge         | Read/Notify | un16 | 0,01  | %       | 0xFFFF     | not available      |
    # +--------------------------------------+-------------------------+-------------+------+-------+---------+------------+--------------------+

    # UUID: (Category, Description, Unit, Multiplier, Signed?, Interpret_function)
    #'6597eeff-4bda-4c1e-af4b-551c4cf74769': ("Latest", "Consumed Ah", "Ah", 10, True, convert_value_number),
    # This one exists as well, but we dont need it:
    # '6597ffff-4bda-4c1e-af4b-551c4cf74769': ("Special", "Keep-alive", "s", 1000, False, lib.helper.convert_value_number),
    MAP = {
        '6597eeff-4bda-4c1e-af4b-551c4cf74769': ("Latest", "Used Energy", "Ah", 10, True, lib.helper.convert_value_number),
        '6597ed8e-4bda-4c1e-af4b-551c4cf74769': ("Latest", "Power", "W", 1, True, lib.helper.convert_value_number),
        '6597ed8d-4bda-4c1e-af4b-551c4cf74769': ("Latest", "Voltage", "V", 100, True, lib.helper.convert_value_number),
        '6597ed8c-4bda-4c1e-af4b-551c4cf74769': ("Latest", "Current", "A", 1000, True, lib.helper.convert_value_number),
        '65970fff-4bda-4c1e-af4b-551c4cf74769': ("Latest", "State Of Charge", "%", 100, False, lib.helper.convert_value_number),
    }

    keep_alive_handle_uuid_map = {
        "b2c4": "6597ffff-4bda-4c1e-af4b-551c4cf74769"
    }

    #read_handle_uuid_map = {
    #    "41a8": "6597eeff-4bda-4c1e-af4b-551c4cf74769",
    #    "ecb8": "6597ed8e-4bda-4c1e-af4b-551c4cf74769",
    #    "da48": "6597ed8d-4bda-4c1e-af4b-551c4cf74769",
    #    "2bd8": "6597ed8c-4bda-4c1e-af4b-551c4cf74769",
    #    "c7c8": "65970fff-4bda-4c1e-af4b-551c4cf74769"
    #}

    read_handle_uuid_map = [
        "65970000-4bda-4c1e-af4b-551c4cf74769"
    ]

    def __init__(self, config):
        self.config = config
        self.count_values = 0

    def get_mapping_table(self):
        return self.MAP

    def get_gatt_device_instance(self, manager, handle_value_function, options):
        return gatt_device_instance(
            manager,
            self.config['mac'],
            handle_value_function=handle_value_function,
            keep_alive=self.keep_alive_handle_uuid_map,
            handle_uuid_map=self.read_handle_uuid_map,
            name=self.config['name'],
            options=options
        )

    def handle_one_value(self, output, characteristic, data):
        """
        Handles the output of a single value, should be given to gatt device on characteistics update
        :param output: Output function
        :param characteristic: Characteristic for the incoming data
        :param data: Incoming data
        :return: Boolean: If last expected device and a disconnect could follow
        """

        if characteristic.uuid not in self.MAP.keys():
            logger.warning(f'{self.config["name"]}: Characteristic ({characteristic.uuid}) not found in known Table')
        else:
            self.count_values += 1
            command = self.MAP[characteristic.uuid]
            result_value = command[5](data, command)
            output(command[1], result_value)

        if self.count_values == len(self.MAP):
            logger.info(f'{self.config["name"]}: Gathering data successful')
            return True
        else:
            return False
