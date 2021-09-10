import json
import gatt
import logging
import lib.helper as helper
from datetime import datetime, timedelta


logger = logging.getLogger()

manager = gatt.DeviceManager(adapter_name="hci0")


class Victron:
    def __init__(self, config, device_config, output, cmd, thread_count, thread_q):
        self.config = config
        self.device_config = device_config
        self.given_output = output
        self.cmd = cmd
        self.thread_count = thread_count
        self.thread_q = thread_q
        self.collections = None
        self.victron_device = None
        self.gatt_device = None

        if self.cmd.collection:
            if device_config['type'] in self.config['collections']:
                self.collections = {}
                for collection in self.config['collections'][device_config['type']].keys():
                    self.reset_collection(collection)

        if self.device_config['protocol'] == 'serial':
            if self.device_config['type'] == 'phoenix':
                from lib.victron_serial.victron_phoenix import Phoenix
                self.victron_device = Phoenix(self.device_config['name'], self.device_config['port'])
            elif self.device_config['type'] == 'smartshunt':
                from lib.victron_serial.victron_smartshunt import Smartshunt
                self.victron_device = Smartshunt(self.device_config['name'], self.device_config['port'])
            elif self.device_config['type'] == 'smartsolar':
                from lib.victron_serial.victron_smartsolar import Smartsolar
                self.victron_device = Smartsolar(self.device_config['name'], self.device_config['port'])

            if self.config['mqtt']['hass']:
                pid, ser, fw = self.victron_device.get_device_info()
                mapping_table = self.victron_device.get_mapping_table()
                helper.send_hass_config_payload(self.device_config['name'],
                                                pid,
                                                ser,
                                                fw,
                                                mapping_table,
                                                self.config['mqtt']['base_topic'],
                                                self.given_output,
                                                self.collections)

        elif self.device_config['protocol'] == 'bluetooth-ble':
            if self.device_config['type'] == 'smartshunt':
                from lib.victron_ble.victron_smartshunt_ble import SmartshuntBLE
                self.victron_device = SmartshuntBLE(self.device_config)

        if self.victron_device is None:
            logger.error(f"{self.device_config['name']}: Missing or unknown device type")
            self.device_finished()


    def read_once(self):
        if self.device_config['protocol'] == 'serial':
            self.victron_device.get_data(self.output)
            self.device_finished()
        else:
            self.create_gatt_device_instance()

            try:
                logger.info(f'{self.device_config["name"]}: Connecting...')
                self.gatt_device.connect()
            except:
                logger.error(f"{self.device_config['name']}: failed to connect. Trying again shortly.")

    def create_gatt_device_instance(self):
        """
        Creates a gatt device
        :return:
        """

        # Here could go another target function than "disconnect after connect_error"!
        #connect_error_target = self.stop_manager
        connect_error_target = self.device_finished

        self.gatt_device = self.victron_device.get_gatt_device_instance(manager, self.handle_value, connect_error_target)

    def device_finished(self):
        logger.debug(f'{self.device_config["name"]}: Thread {self.thread_count} finished')
        self.thread_q.put(f'Thread {self.thread_count} finished')

#    def stop_manager(self):
#        for g_device in manager.devices():
#            if g_device.mac_address == self.device_config['mac']:
#                i = 0
#                while True:
#                    if not g_device.is_connected() or i == 10:
#                        break
#
#                    i += 1
#                    time.sleep(1)
#
#                logger.info(f'{self.device_config["name"]}: device disconnected, stopping gatt manager now!')
#                manager.stop()

    def handle_value(self, characteristics, data):
        last_expected_value = self.victron_device.handle_one_value(self.output, characteristics, data)

        if last_expected_value:
            self.gatt_device.disconnect()

            #self.stop_manager()
            self.device_finished()

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
                    #logger.info(f'Collection is full, sending data via {self.config["logger"]}')
                    logger.debug(f'{self.device_config["name"]}: Collection:  {json.dumps(self.collections[col_key])}')
                    self.given_output(self.device_config["name"], col_key, self.collections[col_key])
