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

well_known_uuids = {
    "00001801-0000-1000-8000-00805f9b34fb": "generic attributes",
    "00001800-0000-1000-8000-00805f9b34fb": "generic access",
    "306b0001-b081-4037-83dc-e59fcc3cdfd0": "vendor, smartsolar & BMV712 ",
    "68c10001-b17f-4d3a-a290-34ad6499937c": "vendor, VE.Direct Smart",
    "97580001-ddf1-48be-b73e-182664615d8e": "vendor, VE.Direct Smart",
}


class AnyDevice(gatt.Device):
    """
    implements event handlers for dbus bt gatt devices
    """

    def __init__(
        self,
        mac_address,
        name,
        manager,
        notification_table,
        ping,
        handle_uuid_map,
        init_sequence_template,
        connect_error_target
    ):
        super().__init__(mac_address, manager, managed=True)
        self.notification_table = notification_table
        self.connected = False
        self.ping = ping
        self.handle_uuid_map = handle_uuid_map
        self.name = name
        self.init_sequence_template = init_sequence_template
        self.connect_error_target = connect_error_target

    def connect_succeeded(self):
        super().connect_succeeded()
        logger.info(f"{self.name}: Connected!")
        self.connected = True
        time.sleep(0)


    def connect_failed(self, error):
        super().connect_failed(error)
        logger.error(f"{self.name}: Connection failed: {str(error)}!")
        self.connected = False
        time.sleep(0)

    def disconnect_succeeded(self):
        super().disconnect_succeeded()
        logger.info(f"{self.name}: Disconnected!")
        time.sleep(0)

    def services_resolved(self):
        super().services_resolved()
        self.connected = True
        logger.debug(f"{self.name}: [{self.mac_address}] Resolved services")
        for service in self.services:
            if service.uuid in well_known_uuids:
                char_name = well_known_uuids[service.uuid]
            else:
                char_name = "unknown endpoint"
            logger.debug(f"[{self.mac_address}] Service [{service.uuid}] ({char_name})")
            for characteristic in service.characteristics:
                logger.debug(f"[{self.mac_address}] Characteristic [{characteristic.uuid}]")
                self.characteristics[characteristic.uuid] = characteristic
        time.sleep(0)

        logger.debug(f'{self.name}: Subscribe to notifications')
        self.subscribe_notifications()
        time.sleep(2)
        logger.debug(f'{self.name}: Send init sequence')
        self.start_send_init_squence()

    def characteristic_enable_notification_succeeded(self, characteristic, value):
        logger.debug(f"{self.name}: enable notification succeded")
        time.sleep(0)

    def characteristic_enable_notification_failed(self, characteristic, value):
        logger.debug(f"{self.name}: enable notification failed")
        time.sleep(0)

    def characteristic_write_value_succeeded(self, characteristic):
        logger.debug(f"{self.name}: write succeeded")
        try:
            self.send_init_sequence()
        except StopIteration:
            pass
        time.sleep(0)

    def characteristic_write_value_failed(self, characteristic, error):
        logger.warning(f"write failed on charactersitic {characteristic.uuid}:merror: {error}")
        time.sleep(0)

    def characteristic_value_updated(self, characteristic, value):
        try:
            if characteristic.uuid in self.notification_table.keys():
                handler_fun = self.notification_table[characteristic.uuid]
                handler_fun(value)
            else:
                logger.debug(
                    f"{self.name}: unhandled characteristic updated: [{characteristic.uuid}]\tvalue:{value}"
                )
        except Exception as e:
            logger.debug(f"UNRECOGNIZED DATA: {self.name}: error handling: {value}: {e}")
        time.sleep(0)

    init_sequence = None
    characteristics = {}

    def subscribe_notifications(self):
        logger.debug(f"{self.name}:subscribe notifications")
        if not self.characteristics:
            logger.debug(f"{self.name}:characteristics empty, sleep & retry - CHECK DEVICE PAIRING!")
            time.sleep(2)
        for key, uuid in self.handle_uuid_map.items():
            try:
                logger.debug(f"{self.name}: notifications for {key}: {uuid}")
                c = self.characteristics[uuid]
                c.enable_notifications()
            except:
                logger.debug(f"{self.name}: error subscribe notification {uuid}")
        logger.debug(f"{self.name}: enable notifications done")
        time.sleep(0)

    def unsubscribe_notifications(self):
        logger.debug(f"{self.name}: Notifications: unsubscribe")
        for key, uuid in self.handle_uuid_map.items():
            try:
                logger.debug(f"{self.name}: Notifications: unsubscribe for {key}: {uuid}")
                c = self.characteristics[uuid]
                c.enable_notifications(enabled=False)
            except:
                logger.warning(f"{self.name}: Notifications: unsubscribe failed: {uuid}")
        #print(f"{self.name}: disnable notifications done")
        time.sleep(0)

    def start_send_init_squence(self):
        global init_sequence
        init_sequence = self.init_sequence_template()
        self.send_init_sequence()

    def send_init_sequence(self):
        (uuid, handle, data) = next(init_sequence)
        if not self.characteristics:
            self.characteristics_missing()
        c = self.characteristics[uuid]
        logger.debug(f"{self.name}: sending {handle}, data{data}")
        c.write_value(data)
        time.sleep(1)

    def characteristics_missing(self):
        logger.debug(f"{self.name}: connected but characteristics not yet enumerated, sleep an retry")
        logger.debug(f"{self.name}: CHECK DEVICE PAIRING!")
        time.sleep(2)
        self.start_send_init_squence()

    def send_ping(self):
        logger.debug(f"{self.name}: send ping")
        for packet in self.ping:
            c = self.characteristics[self.handle_uuid_map[packet[0]]]
            hs = packet[1]
            b = bytearray.fromhex(hs)
            logger.debug(f"{self.name}: sending {packet[0]}, data{b}")
            c.write_value(b)
        logger.debug(f"{self.name}: send ping done")


def gatt_device_instance(manager, mac, name, notification_table, ping, handle_uuid_map, init_sequence_template, connect_error_target):
    return AnyDevice(
        mac,
        name,
        manager=manager,
        notification_table=notification_table,
        ping=ping,
        handle_uuid_map=handle_uuid_map,
        init_sequence_template=init_sequence_template,
        connect_error_target=connect_error_target
    )
