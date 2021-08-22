import gatt
import logging
import time
#import victron_smartshunt_ble
import lib.victron_ble.victron_smartshunt_ble as victron_smartshunt_ble

logger = logging.getLogger()

manager = gatt.DeviceManager(adapter_name="hci0")


class Victron:
    def __init__(self, config, output, cmd, thread_count, thread_q):
        self.config = config
        self.output = output
        self.cmd = cmd
        self.thread_count = thread_count
        self.thread_q = thread_q
        self.victron_device = None
        self.gatt_device = None

    def read_once(self):
        self.create_victron_device_instance(self.config)
        self.create_gatt_device_instance()

        try:
            logger.info(f'{self.config["name"]}: Connecting...')
            self.gatt_device.connect()
        except:
            logger.error(f"{self.config['name']}: failed to connect. Trying again shortly.")

    def create_victron_device_instance(self, device_config):
        self.victron_device = victron_smartshunt_ble.SmartshuntBLE(device_config)

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
        logger.debug(f'{self.config["name"]}: Thread {self.thread_count} finished')
        self.thread_q.put(f'Thread {self.thread_count} finished')

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

            #self.stop_manager()
            self.device_finished()
