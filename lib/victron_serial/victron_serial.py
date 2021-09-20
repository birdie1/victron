import logging
import time

logger = logging.getLogger()


class VictronSerial:
    def __init__(self, device_config, output):
        self.device_config = device_config
        self.output = output
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
        logger.debug(f'{self.device_config["name"]}: Finished')

    def connect_disconnect_loop(self, args, timer):
        while True:
            self.victron_device.get_data(self.output)

            if args.direct_disconnect:
                self.finished_target()
            else:
                time.sleep(timer['serial']['repeat'])
