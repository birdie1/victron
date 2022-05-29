import gatt
import logging
import time
from datetime import datetime, timedelta

logger = logging.getLogger()
manager = gatt.DeviceManager(adapter_name="hci0")


class VictronBle:
    def __init__(self, device_config, output):
        self.device_config = device_config
        self.victron_device = None
        self.gatt_device = None
        self.output = output

        if self.device_config['type'] == 'smartshunt':
            from lib.victron_ble.victron_smartshunt_ble import SmartshuntBLE
            self.victron_device = SmartshuntBLE(self.device_config)
        else:
            logger.error(f'Got unknown type ({self.device_config["type"]}) from config!')

    @staticmethod
    def get_device_info():
        pid = "Currently not available via BLE"
        ser = "Currently not available via BLE"
        fw = "Currently not available via BLE"
        return pid, ser, fw

    def get_mapping_table(self):
        return self.victron_device.get_mapping_table()

    def handle_value(self, characteristics, data):
        last_expected_value = self.victron_device.handle_one_value(self.output, characteristics, data)

        if last_expected_value:
            logger.debug(f'{self.device_config["name"]}: Got last value, disconnecting...')
            self.gatt_device.disconnect()

    def connect_loop(self):
        manager.start_discovery()
        time.sleep(1)

        try:
            logger.info(f'{self.device_config["name"]}: Connecting...')
            self.gatt_device.connect()
        except:
            logger.error(f'{self.device_config["name"]}: failed to connect. Trying again shortly.')
            return False
        finally:
            manager.stop_discovery()

        if not self.gatt_device.connected:
            return False
        else:
            manager.run()
            return True

    def connect_disconnect_loop(self, args, timer):
        options = {
            'direct_disconnect': args.direct_disconnect
        }
        self.gatt_device = self.victron_device.get_gatt_device_instance(
            manager,
            self.handle_value,
            options
        )

        while True:
            if self.connect_loop():
                if args.direct_disconnect:
                    logger.debug(f'{self.device_config["name"]}: Direct disconnect enabled. Exiting...')
                    break
                else:
                    next_time = datetime.now() + timedelta(seconds=timer['bluetooth-ble']['repeat'])
                    logger.debug(f'{self.device_config["name"]}: Will reconnect at {next_time}')
                    time.sleep(timer['bluetooth-ble']['repeat'])
            else:
                time.sleep(timer['retry'])
