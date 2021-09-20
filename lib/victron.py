import json
import logging
import lib.helper as helper
from datetime import datetime, timedelta

logger = logging.getLogger()


class Victron:
    def __init__(self, config, device_config, output, cmd, thread_count, thread_q):
        self.config = config
        self.device_config = device_config
        self.given_output = output
        self.cmd = cmd
        self.thread_count = thread_count
        self.thread_q = thread_q
        self.collections = None
        self.victron_type = None

        if self.cmd.collection:
            if device_config['type'] in self.config['collections']:
                self.collections = {}
                for collection in self.config['collections'][device_config['type']].keys():
                    self.reset_collection(collection)

        if self.device_config['protocol'] == 'serial':
            from lib.victron_serial.victron_serial import VictronSerial
            self.victron_type = VictronSerial(device_config, self.output)
        elif self.device_config['protocol'] == 'bluetooth-ble':
            from lib.victron_ble.victron_ble import VictronBle
            self.victron_type = VictronBle(device_config, self.output)
        elif self.device_config['protocol'] == 'bluetooth':
            from lib.victron_bluetooth.victron_bluetooth import VictronBluetooth
            self.victron_type = VictronBluetooth(device_config, self.output)

        if self.victron_type is None:
            logger.error(f"{self.device_config['name']}: Missing or unknown device type")

        if self.config['mqtt']['hass'] and self.config['logger'] == 'mqtt':
            pid, ser, fw = self.victron_type.get_device_info()
            mapping_table = self.victron_type.get_mapping_table()
            helper.send_hass_config_payload(self.device_config['name'],
                                            pid,
                                            ser,
                                            fw,
                                            mapping_table,
                                            self.config['mqtt']['base_topic'],
                                            self.given_output,
                                            self.collections)

    def connect_disconnect_loop(self):
        self.victron_type.connect_disconnect_loop(self.cmd, self.config['timer'])

    def reset_collection(self, collection_name):
        collection = {}
        for item in self.config['collections'][self.device_config['type']][collection_name]:
            collection[item] = None
        self.collections[collection_name] = collection

    def collection_check_full(self, collection):
        for value in collection.values():
            if value is None:
                return False
        return True

    def set_value_in_collections(self, value_name, value):
        for col_key in self.collections.keys():
            if value_name in self.collections[col_key]:
                self.collections[col_key][value_name] = value
                self.collections[col_key][f'{value_name} Updated'] = f'{datetime.now():%Y-%m-%d %H:%M:%S}'
                logger.debug(f'{self.device_config["name"]}: Setting value in collection: {value_name} to {value}')
                return col_key
        return False

    def output(self, category, value):
        if not self.cmd.collection:
            self.given_output(self.device_config['name'], category, value)
        else:
            col_key = self.set_value_in_collections(category, value)
            if not col_key:
                logger.debug(
                    f'{self.device_config["name"]}: {category} not in any collections, it will never be published')
            else:
                if self.collection_check_full(self.collections[col_key]):
                    logger.debug(f'{self.device_config["name"]}: Collection:  {json.dumps(self.collections[col_key])}')
                    self.given_output(self.device_config["name"], col_key, self.collections[col_key])
