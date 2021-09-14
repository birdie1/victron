import logging

logger = logging.getLogger()

class VictronSerial:
    def __init__(self, device_config):
        self.device_config = device_config
        self.victron_device = None

        if self.device_config['type'] == 'phoenix':
            from lib.victron_serial.victron_phoenix import Phoenix
            self.victron_device = Phoenix(self.device_config['name'], self.device_config['port'])
        elif self.device_config['type'] == 'smartshunt':
            from lib.victron_serial.victron_smartshunt import Smartshunt
            self.victron_device = Smartshunt(self.device_config['name'], self.device_config['port'])
        elif self.device_config['type'] == 'smartsolar':
            from lib.victron_serial.victron_smartsolar import Smartsolar
            self.victron_device = Smartsolar(self.device_config['name'], self.device_config['port'])
        else:
            logger.error(f'Got unknown type ({self.device_config["type"]}) from config!')

    def get_device_info(self):
        return self.victron_device.get_device_info()

    def get_mapping_table(self):
        return self.victron_device.get_mapping_table()

    def finished_target(self):
        logger.debug(f'{self.device_config["name"]}: Thread {self.thread_count} finished')

    def read(self, output):
        self.victron_device.get_data(output)
        self.finished_target()
