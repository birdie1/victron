"""
interface classes for victron devices using pygatt
all async event driven
"""
import gatt
from gatt.gatt_linux import Characteristic
import threading


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


def init_sequence_template():
    stuff = [
        ("0021", "fa80ff"),
        ("0021", "f980"),
        ("0024", "01"),
        ("0024", "0300"),  # triggers undecoded responses 0x080318 0x080319 && 0xffff
        ########### taken from phoenix
        # ("0024", "060082189342102703010303"),  # send voltage, power, current
        # ("0021", "f941"),  # taken from phoenix, sends power & current
        ########## end taken from phoenix
        ("0024", "060082189342102703010303"),
        ("0027", "05008119010905008119010a05008119ec0f0500"),
        ("0027", "8119ec0e05008119010c050081189005008119ec"),
        ("0024", "3f05008119ec12"),
        ("0027", "0501811901000501811901000501811901000501"),
        ("0027", "8119010905018119010a05038119010905038119"),
        ("0027", "010a05038119010205038119ec0f05038119ec0e"),
        ("0027", "050381190110050381190fff0503811818050381"),
        ("0027", "19ed8d05038119ed8f05038119ed8c05038119ee"),
        ("0027", "ff05038119ed7d050381190383050381190ffe05"),
        ("0027", "038119034e05038119edec050381190300050381"),
        ("0024", "190301050381190302050381190305"),
        ("0027", "05038119030605038119030705038119030e0503"),
        ("0027", "8119030f05038119031005038119031105038119"),
        ("0027", "030a05038119030b050381190303050381190308"),
        ("0027", "0503811903090503811903040503811910300503"),
        ("0027", "8119031d05038119031e05038119eefc05038119"),
        ("0027", "0328050381190329050381190320050381190321"),
        ("0027", "0503811903220503811903230503811903240503"),
        ("0024", "81190325050381190326050381190327"),
        ("0027", "05038119032c05038119032d05038119032a0503"),
        ("0027", "8119032b05038119033105038119033205038119"),
        ("0027", "034f05038119034d05038119100a05038119100b"),
        ("0027", "0503811910090503811903500503811903510503"),
        ("0027", "8119035205038119035305038119035405038119"),
        ("0027", "035505038119035605038119035705038119035c"),
        ("0027", "05038119035d05038119035a05038119035b0503"),
        ("0024", "81190361050381190362050381191000"),
        ("0027", "0503811910010503811910020503811910030503"),
        ("0027", "8119100505038119100405038119100605038119"),
        ("0027", "100705038119102c050381191029050381190ffd"),
        ("0027", "05038119100805038119eefe0503811904000503"),
        ("0027", "8119eef505038119eee005038119eee305038119"),
        ("0027", "eee805038119eee405038119eee505038119eee6"),
        ("0027", "05038119eee105038119eee705038119eee20503"),
        ("0024", "8119eef605038119eef805038119eefb"),
        ("0021", "f941"),
        ("0027", "05038119eefa05038119eef705038119eef40503"),
        ("0027", "8119015005038118900503811891050381040503"),
        ("0027", "8119103405038119ec3f05038119ec1205008119"),
        ("0027", "ec1305008119ec1405008119ec1505008119ec16"),
        ("0027", "0501811901020501811901420501811890050181"),
        ("0027", "19ec3f05018119ec1205018119010205018119ec"),
        ("0024", "0f05018119ec0e05018119010c050181190110"),
        ("0024", "05008119ec20"),
        ("0024", "05008119ec17"),
        # separat deutlich später
        ("0024", "060382191000426300"),
        ############nex try
        # ("0021", "f941"),
        # ("0027", "05038119eefa05038119eef705038119eef40503"),
        # ("0027", "8119015005038118900503811891050381040503"),
        # ("0027", "8119103405038119ec3f05038119ec1205008119"),
        # ("0027", "ec1305008119ec1405008119ec1505008119ec16"),
        # ("0027", "0501811901020501811901420501811890050181"),
        # ("0027", "19ec3f05018119ec1205018119010205018119ec"),
        # ("0027", "0f05018119ec0e05018119010c050181190110"),
        ############# short seuqence without f941
        # ("0024", "05008119ec20"),
        # ("0024", "05008119ec17"),
    ]
    for packet in stuff:
        c = characteristics[smart_shunt_ids[packet[0]]]
        hs = packet[1]
        b = bytearray.fromhex(hs)
        yield (c, b)


ping = [
    ("0024", "0300"),
    ("0021", "f941"),  # taken from phoenix, sends power & current
]

smart_shunt_ids = {
    # service 0x 52
    "0027": "306b0004-b081-4037-83dc-e59fcc3cdfd0",  # 1
    "0024": "306b0003-b081-4037-83dc-e59fcc3cdfd0",  # 2
    "0021": "306b0002-b081-4037-83dc-e59fcc3cdfd0",  # 3
    # service 0x12
    "001d": "97580006-ddf1-48be-b73e-182664615d8e",  # 4
    "001d": "97580004-ddf1-48be-b73e-182664615d8e",  # 5
    "0018": "97580003-ddf1-48be-b73e-182664615d8e",  # 6
    "": "97580002-ddf1-48be-b73e-182664615d8e",  # 7 fehlt
    # service 0x 52
    "0013": "68c10003-b17f-4d3a-a290-34ad6499937c",  # 8
    # service 0x 12
    "0010": "68c10002-b17f-4d3a-a290-34ad6499937c",  # 9
    "": "00002a05-0000-1000-8000-00805f9b34fb",  # 10 fehlt
}


init_sequence = None


def start_send_init_squence():
    global init_sequence
    init_sequence = init_sequence_template()
    send_init_sequence()


def send_init_sequence():
    (c, b) = next(init_sequence)
    print(f"sending {c.uuid}, data{b}")
    c.write_value(b)


def send_ping():
    print("send ping")
    for packet in ping:
        c = characteristics[smart_shunt_ids[packet[0]]]
        hs = packet[1]
        b = bytearray.fromhex(hs)
        print(f"sending {c.uuid}, data{b}")
        c.write_value(b)
    print("send ping done")


services = {
    "00001801-0000-1000-8000-00805f9b34fb": "generic attributes",
    "00001800-0000-1000-8000-00805f9b34fb": "generic access",
    "306b0001-b081-4037-83dc-e59fcc3cdfd0": "vendor, smartsolar & BMV712 ",
    "68c10001-b17f-4d3a-a290-34ad6499937c": "vendor, VE.Direct Smart",
    "97580001-ddf1-48be-b73e-182664615d8e": "vendor, VE.Direct Smart",
}

characteristics = {}


def subscribe_notifications():
    print("subscribe notifications")
    for key, c in characteristics.items():
        # nachgucken was c so anbietet. gibt es handles?
        print(f"notificaions for end={c.uuid}")
        c.enable_notifications()
    print("enable notifications done")


class AnyDevice(gatt.Device):
    def __init__(self, mac_address, manager, notification_table):
        super().__init__(mac_address, manager, managed=True)
        self.notification_table = notification_table
        self.connected = False

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
            print(
                "[%s]  Service [%s] (%s)"
                % (self.mac_address, service.uuid, services[service.uuid])
            )
            for characteristic in service.characteristics:
                print(
                    "[%s]    Characteristic [%s]"
                    % (self.mac_address, characteristic.uuid)
                )
                characteristics[characteristic.uuid] = characteristic

    def characteristic_enable_notification_succeeded(self, characteristic, value):
        print("enable notification succeded")

    def characteristic_enable_notification_failed(self, characteristic, value):
        print("enable notification failed")

    def characteristic_write_value_succeeded(self, characteristic):
        print("write succeeded")
        try:
            send_init_sequence()
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


def get_device_instance(mac, notification_table):
    return AnyDevice(mac, manager=manager, notification_table=notification_table)


# init event loop
manager = gatt.DeviceManager(adapter_name="hci0")

print("start")

print("manager thread")
t1 = threading.Thread(target=lambda: manager.run())
t1.daemon = True
t1.start()
print("manager running")