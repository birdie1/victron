import gatt
import logging
import time

logger = logging.getLogger()
manager = gatt.DeviceManager(adapter_name="hci0")


class VictronBle:
    def __init__(self, device_config):
        self.device_config = device_config
        self.victron_device = None
        self.gatt_device = None
        self.output = None

        if self.device_config['type'] == 'smartshunt':
            from lib.victron_ble.victron_smartshunt_ble import SmartshuntBLE
            self.victron_device = SmartshuntBLE(self.device_config)
        else:
            logger.error(f'Got unknown type ({self.device_config["type"]}) from config!')

    def get_device_info(self):
        pass

    def get_mapping_table(self):
        pass

    def finished_target(self):
        self.gatt_device.disconnect()
        logger.debug(f'{self.device_config["name"]}: Thread finished')
        manager.stop()

    def handle_value(self, characteristics, data):
        last_expected_value = self.victron_device.handle_one_value(self.output, characteristics, data)

        if last_expected_value:
            logger.debug(f'{self.device_config["name"]}: Got last value, disconnecting...')
            self.finished_target()

    def read(self, output):
        self.output = output

        self.gatt_device = self.victron_device.get_gatt_device_instance(
            manager,
            self.handle_value,
            self.finished_target
        )

        manager.start_discovery()
        time.sleep(2)

        try:
            logger.info(f'{self.device_config["name"]}: Connecting...')
            self.gatt_device.connect()
        except:
            logger.error(f"{self.device_config['name']}: failed to connect. Exiting...")
        finally:
            manager.stop_discovery()

        manager.run()
