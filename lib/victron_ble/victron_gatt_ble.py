"""
interface classes for victron devices using pygatt
all async event driven
"""
from time import sleep
import gatt
from gatt.gatt_linux import Characteristic
import logging
import threading
import time

logger = logging.getLogger()


class AnyDevice(gatt.Device):
    """
    implements event handlers for dbus bt gatt devices
    """

    def __init__(
        self,
        mac_address,
        name,
        manager,
        handle_value_function,
        keep_alive,
        handle_uuid_map,
        connect_error_target
    ):
        super().__init__(mac_address, manager, managed=True)
        self.handle_value_function = handle_value_function
        self.connected = False
        self.keep_alive = keep_alive
        self.handle_uuid_map = handle_uuid_map
        self.name = name
        self.connect_error_target = connect_error_target

    def connect_succeeded(self):
        super().connect_succeeded()
        logger.info(f"{self.name}: Connect successful!")
        self.connected = True
        time.sleep(0)

    def connect_failed(self, error):
        super().connect_failed(error)
        logger.error(f"{self.name}: Connection failed: {str(error)}!")
        self.connected = False
        self.connect_error_target()
        time.sleep(0)

    def disconnect_succeeded(self):
        super().disconnect_succeeded()
        logger.info(f"{self.name}: Disconnect successful!")
        time.sleep(0)

    def characteristic_write_value_succeeded(self, characteristic):
        logger.debug(f"{self.name}: write succeeded")
        time.sleep(0)

    def characteristic_write_value_failed(self, characteristic, error):
        logger.warning(f"write failed on charactersitic {characteristic.uuid} | merror: {error}")
        time.sleep(0)

    def services_resolved(self):
        super().services_resolved()
        self.connected = True
        logger.debug(f"{self.name}: [{self.mac_address}] Resolved services")
        for service in self.services:
            if service.uuid in self.handle_uuid_map:
                for characteristic in service.characteristics:
                    characteristic.read_value()
        time.sleep(0)

    def characteristic_value_updated(self, characteristic, value):
        try:
            self.handle_value_function(characteristic, value)
        except Exception as e:
            logger.debug(f"UNRECOGNIZED DATA: {self.name}: error handling: {value}: {e}")
        time.sleep(0)

    def set_keep_alive(self):
        for service in self.services:
            if service.uuid in self.keep_alive:
                ## 60 seconds!
                service.write_value("60ea")



def gatt_device_instance(manager, mac, name, handle_value_function, keep_alive, handle_uuid_map, connect_error_target):
    return AnyDevice(
        mac,
        name,
        manager=manager,
        handle_value_function=handle_value_function,
        keep_alive=keep_alive,
        handle_uuid_map=handle_uuid_map,
        connect_error_target=connect_error_target
    )



