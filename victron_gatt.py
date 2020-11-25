"""
interface classes for victron devices using pygatt
all async event driven
"""
import gatt
from gatt.gatt_linux import Characteristic
import threading
import time

logger_name = "x"


# def find_characteristics_handles():
# print("try charcteristics")
# hs = "fa80ff"
# b = bytearray.fromhex(hs)
# count = 1
# for key, value in characteristics.items():
#     hs = f"fa80f{count:x}"
#     count += 1
#     b = bytearray.fromhex(hs)
#     print(f"trying char {key}")
#     value.write_value(b)

well_known_uuids = {
    "00001801-0000-1000-8000-00805f9b34fb": "generic attributes",
    "00001800-0000-1000-8000-00805f9b34fb": "generic access",
    "306b0001-b081-4037-83dc-e59fcc3cdfd0": "vendor, smartsolar & BMV712 ",
    "68c10001-b17f-4d3a-a290-34ad6499937c": "vendor, VE.Direct Smart",
    "97580001-ddf1-48be-b73e-182664615d8e": "vendor, VE.Direct Smart",
}


class AnyDevice(gatt.Device):
    def __init__(
        self,
        mac_address,
        name,
        manager,
        notification_table,
        ping,
        handle_uuid_map,
        init_sequence_template,
    ):
        super().__init__(mac_address, manager, managed=True)
        self.notification_table = notification_table
        self.connected = False
        self.ping = ping
        self.handle_uuid_map = handle_uuid_map
        self.name = name
        self.init_sequence_template = init_sequence_template

    def connect_succeeded(self):
        super().connect_succeeded()
        print("[%s] Connected" % (self.mac_address))
        self.connected = True

    def connect_failed(self, error):
        super().connect_failed(error)
        print("[%s] Connection failed: %s" % (self.mac_address, str(error)))
        self.connected = False

    def disconnect_succeeded(self):
        super().disconnect_succeeded()
        print("[%s] Disconnected" % (self.mac_address))

    def services_resolved(self):
        super().services_resolved()
        self.connected = True
        print("[%s] Resolved services" % (self.mac_address))
        for service in self.services:
            if service.uuid in well_known_uuids:
                char_name = well_known_uuids[service.uuid]
            else:
                char_name = "unknown endpoint"
            print(
                "[%s]  Service [%s] (%s)" % (self.mac_address, service.uuid, char_name)
            )
            for characteristic in service.characteristics:
                print(
                    "[%s]    Characteristic [%s]"
                    % (self.mac_address, characteristic.uuid)
                )
                self.characteristics[characteristic.uuid] = characteristic

    def characteristic_enable_notification_succeeded(self, characteristic, value):
        print("enable notification succeded")

    def characteristic_enable_notification_failed(self, characteristic, value):
        print("enable notification failed")

    def characteristic_write_value_succeeded(self, characteristic):
        print("write succeeded")
        try:
            self.send_init_sequence()
        except StopIteration:
            pass

    def characteristic_write_value_failed(self, characteristic, error):
        print(f"write failed on charactersitic {characteristic.uuid}:merror: {error}")

    def characteristic_value_updated(self, characteristic, value):
        try:
            if characteristic.uuid == "0000180a-0000-1000-8000-00805f9b34fb":
                print("Firmware version:", value.decode("utf-8"))

            if characteristic.uuid in self.notification_table.keys():
                handler_fun = self.notification_table[characteristic.uuid]
                handler_fun(value)
            else:
                print(
                    f"unhandled characteristic updated: [{characteristic.uuid}]\tvalue:{value}"
                )
        except:
            print(f"error handling: {value}")

    def request_firmware_Version(self):
        try:
            device_information_service = next(
                s
                for s in self.services
                if s.uuid == "0000180a-0000-1000-8000-00805f9b34fb"
            )
        except StopIteration:
            print("no firmware characteristic avlbl")
            return

        firmware_version_characteristic = next(
            c
            for c in device_information_service.characteristics
            if c.uuid == "00002a26-0000-1000-8000-00805f9b34fb"
        )

        firmware_version_characteristic.read_value()

    init_sequence = None
    characteristics = {}

    def subscribe_notifications(self):
        print("subscribe notifications")
        for key, c in self.characteristics.items():
            # nachgucken was c so anbietet. gibt es handles?
            print(f"notificaions for end={c.uuid}")
            c.enable_notifications()
        print("enable notifications done")

    def start_send_init_squence(self):
        global init_sequence
        init_sequence = self.init_sequence_template()
        self.send_init_sequence()

    def send_init_sequence(self):
        (uuid, handle, data) = next(init_sequence)
        if uuid not in self.characteristics:
            # this should not happen. send_init is triggered before characteristics are complete
            self.characteristics_missing()
        c = self.characteristics[uuid]
        print(f"sending {handle}, data{data}")
        c.write_value(data)
        time.sleep(1)

    def characteristics_missing(self):
        print(f"connected but characteristics not yet enumerated, sleep an retry")
        time.sleep(2)
        self.start_send_init_squence()

    def send_ping(self):
        print("send ping")
        for packet in self.ping:
            c = self.characteristics[self.handle_uuid_map[packet[0]]]
            hs = packet[1]
            b = bytearray.fromhex(hs)
            print(f"sending {packet[0]}, data{b}")
            c.write_value(b)
        print("send ping done")


def gatt_device_instance(
    mac, name, notification_table, ping, handle_uuid_map, init_sequence_template
):
    return AnyDevice(
        mac,
        name,
        manager=manager,
        notification_table=notification_table,
        ping=ping,
        handle_uuid_map=handle_uuid_map,
        init_sequence_template=init_sequence_template,
    )


# init event loop
manager = gatt.DeviceManager(adapter_name="hci0")

print("start")

print("manager thread")
t1 = threading.Thread(target=lambda: manager.run())
t1.daemon = True
t1.start()
print("manager running")