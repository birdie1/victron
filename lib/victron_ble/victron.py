import logging
import time
#import victron_smartshunt_ble
import lib.victron_ble.victron_smartshunt_ble as victron_smartshunt_ble
from lib.victron_ble.victron_gatt_ble import manager

logger = logging.getLogger()


class VictronBLE:
    def __init__(self, config, output):
        self.config = config
        self.output = output
        self.victron_device = None
        self.gatt_device = None

    def read_once(self):
        self.create_victron_device_instance(self.config)
        self.create_gatt_device_instance()

        try:
            self.gatt_device.connect()
        except:
            logger.error(f"{self.config['name']}: failed to connect. Trying again shortly.")

    def create_victron_device_instance(self, device_config):
        self.victron_device = victron_smartshunt_ble.Smartshunt(device_config)

    def create_gatt_device_instance(self):
        self.gatt_device = self.victron_device.get_gatt_device_instance(self.handle_value)

    def stop_manager(self):
        for g_device in manager.devices():
            if g_device.mac_address == self.config['mac']:
                i = 0
                while True:
                    if not g_device.is_connected() or i == 10:
                        break

                    i += 1
                    time.sleep(1)

                logger.info(f'{self.config["name"]}: device disconnected, stopping gatt manager now!')
                manager.stop()

    def handle_value(self, characteristics, data):
        last_expected_value = self.victron_device.handle_one_value(self.output, characteristics, data)

        if last_expected_value:
            self.gatt_device.disconnect()

            self.stop_manager()
