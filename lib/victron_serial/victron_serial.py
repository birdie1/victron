import logging
import time
import threading
from vedirect import Vedirect

logger = logging.getLogger()

# hack! patch vedirect's read_data_callback method to support exiting the main loop

#vedirect.read_data_callback = lambda self, callbackFunction:
def read_data_callback(self, callbackFunction):
    self.keep_running = True
    while self.keep_running:
        data = self.ser.read()
        for byte in data:
            packet = self.input(byte)
            if (packet != None):
                callbackFunction(packet)
Vedirect.read_data_callback = read_data_callback

class VictronSerial:
    def __init__(self, device_config, output_callback):
        self.device_config = device_config
        self.output_callback = output_callback
        self.name = device_config['name']
        self.type = device_config['type']
        self.port = device_config['port']

        if self.type == 'phoenix':
            from lib.victron_serial.victron_phoenix import value_description_map
        elif self.type == 'smartshunt':
            from lib.victron_serial.victron_smartshunt import value_description_map
        elif self.type == 'smartsolar':
            from lib.victron_serial.victron_smartsolar import value_description_map
        else:
            raise RuntimeError(f'Got unknown type ({self.type}) from config!')
        self.map = value_description_map

        self.ve = Vedirect(self.port, 60)
        callback_wrapper = lambda packet: self.read_data_callback(packet)
        self.thread = threading.Thread(target=self.ve.read_data_callback, args=(callback_wrapper,))
        self.thread.start()
        # TODO: stop this thread when the application quits

        self.last_packet = None
        self.last_packet_ready = threading.Event()
        self.timer_elapsed = True

    def get_device_info(self):
        data = None
        while data is None:
            self.last_packet_ready.wait()
            self.last_packet_ready.clear()
            # on startup, sometimes incomplete packets show up
            if all([x in self.last_packet for x in ['PID', 'FW']]):
                data = self.last_packet
            else:
                logging.info('Skipping incomplete packet, waiting for next packet for device info')
        pid = self.map['PID'][4](data['PID'], self.map['PID'])
        if 'SER#' in self.map:
            ser = self.map['SER#'][4](data['SER#'], self.map['SER#'])
        else:
            ser = "SER# NOT SUPPORTED"
        fw = self.map['FW'][4](data['FW'], self.map['FW'])
        return pid, ser, fw

    def get_mapping_table(self):
        return self.map

    def finished_target(self):
        logger.debug(f'{self.name} finished')

    def connect_disconnect_loop(self, args, timer):
        logger.debug("Executing connect_disconnect_loop in victron_serial")
        while True:
            if args.direct_disconnect:
                self.last_packet_ready.wait()
                self.last_packet_ready.clear()
                self.shutdown()
                self.finished_target()
                return
            else:
                try:
                    time.sleep(timer['serial']['repeat'])
                except KeyboardInterrupt:
                    self.shutdown()
                    raise
                self.timer_elapsed = True

    def shutdown(self):
        if hasattr(self.ve, 'keep_running'):
            logging.info(f'Shutting down {self.name} thread')
            self.ve.keep_running = False
            self.thread.join()

    def read_data_callback(self, packet):
        logger.debug(f'Got data from port {self.port}: {packet}')
        self.last_packet = packet
        self.last_packet_ready.set()

        if self.timer_elapsed:
            self.timer_elapsed = False
            self.process_packet(packet)

    def process_packet(self, packet):
        logger.debug(f'Processing packet with {len(packet)} items')
        for key, value in packet.items():
            # for devices with a serial number, extract the production date as additional property
            if key == 'SER#':
                self.send_out('PROD', value)
            self.send_out(key, value)

    def send_out(self, key, value):
        if key not in self.map:
            logger.warning(f'{self.name}: {key} not found in mapping dictionary')
            return
        map_entry = self.map[key]
        category, description, unit, factor, helper_function = map_entry
        data = helper_function(value, map_entry)
        self.output_callback(description, data, unit)

