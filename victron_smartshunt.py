import sys
from os import name
from victron_gatt import AnyDevice, gatt_device_instance


class Smartshunt:

    ping = [
        ("0024", "0300"),
        ("0021", "f941"),  # taken from phoenix, sends power & current
    ]

    handle_uuid_map = {
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

    def __init__(self, config):
        self.config = config
        self.gatt_device = None
        self.collections = {}

        for collection in self.config['collections']['smartshunt'].keys():
            self.reset_collection(collection)

    def reset_collection(self, collection_name):
        collection = {}
        for item in self.config['collections']['smartshunt'][collection_name]:
            collection[item] = None
        self.collections[collection_name] = collection

    def get_gatt_device_instance(self, mac, name, handle_single_value, handle_bulk_values):
        UUID_FUNCTION_TABLE = {
            self.handle_uuid_map["0027"]: handle_bulk_values,
            self.handle_uuid_map["0024"]: handle_single_value,
            self.handle_uuid_map["0021"]: handle_single_value,
        }

        self.gatt_device = gatt_device_instance(
            mac,
            notification_table=UUID_FUNCTION_TABLE,
            ping=self.ping,
            handle_uuid_map=self.handle_uuid_map,
            name=name,
            init_sequence_template=self.init_sequence_template,
            device_class=self,
        )
        return self.gatt_device

    def init_sequence_template(self):
        stuff = [
            ("0021", "fa80ff"),
            ("0021", "f980"),
            ("0024", "01"),
            ("0024", "0300"),  # triggers undecoded responses 0x080318 0x080319 && 0xffff
            ########### taken from phoenix
            # ("0024", "060082189342102703010303"),  # send voltage, power, current
            # ("0021", "f941"),  # taken from phoenix, sends power & current
            ########## end taken from phoenix
            ############ copied from wireshark "change_values.pcapng"
            ("0024", "060082189342102703010303"),
            ("0027", "05008119010905008119010a05008119ec0f0500"),
            ("0027", "8119ec0e05008119010c050081189005008119ec"),
            ("0024", "3f05008119ec12"),
            ("0027", "0501811901000501811901000501811901000501"),
            ("0027", "8119010905018119010a05038119010905038119"),
            ("0027", "010a05038119010205038119ec0f05038119ec0e"),
            # scheinen wichtig, wegen battery status
            ("0027", "050381190110050381190fff0503811818050381"),
            ("0027", "19ed8d05038119ed8f05038119ed8c05038119ee"),
            ("0027", "ff05038119ed7d050381190383050381190ffe05"),
            ("0027", "038119034e05038119edec050381190300050381"),
            ("0024", "190301050381190302050381190305"),
            # scheinen unwichtig, schon länger aus
            # ("0027", "05038119030605038119030705038119030e0503"),
            # ("0027", "8119030f05038119031005038119031105038119"),
            # ("0027", "030a05038119030b050381190303050381190308"),
            # ("0027", "0503811903090503811903040503811910300503"),
            # ("0027", "8119031d05038119031e05038119eefc05038119"),
            # ("0027", "0328050381190329050381190320050381190321"),
            # ("0027", "0503811903220503811903230503811903240503"),
            ### disconnected
            ("0024", "81190325050381190326050381190327"),
            # versuch zu reduzieren, alle 0x0027 ausgebldendet
            # ("0027", "05038119032c05038119032d05038119032a0503"),
            # ("0027", "8119032b05038119033105038119033205038119"),
            # ("0027", "034f05038119034d05038119100a05038119100b"),
            # ("0027", "0503811910090503811903500503811903510503"),
            # ("0027", "8119035205038119035305038119035405038119"),
            # ("0027", "035505038119035605038119035705038119035c"),
            # ("0027", "05038119035d05038119035a05038119035b0503"),
            ("0024", "81190361050381190362050381191000"),
            # ("0027", "0503811910010503811910020503811910030503"),
            # ("0027", "8119100505038119100405038119100605038119"),
            # ("0027", "100705038119102c050381191029050381190ffd"),
            # ("0027", "05038119100805038119eefe0503811904000503"),
            # ("0027", "8119eef505038119eee005038119eee305038119"),
            # ("0027", "eee805038119eee405038119eee505038119eee6"),
            # ("0027", "05038119eee105038119eee705038119eee20503"),
            ("0024", "8119eef605038119eef805038119eefb"),
            ("0021", "f941"),
            # ("0027", "05038119eefa05038119eef705038119eef40503"),
            # ("0027", "8119015005038118900503811891050381040503"),
            # ("0027", "8119103405038119ec3f05038119ec1205008119"),
            # ("0027", "ec1305008119ec1405008119ec1505008119ec16"),
            # ("0027", "0501811901020501811901420501811890050181"),
            # ("0027", "19ec3f05018119ec1205018119010205018119ec"),
            # ("0024", "0f05018119ec0e05018119010c050181190110"),
            ("0024", "05008119ec20"),
            ("0024", "05008119ec17"),
            # separat deutlich später
            ("0024", "060382191000426300"),
            ########### END copied from wireshark
        ]
        for packet in stuff:
            handle = packet[0]
            uuid = self.handle_uuid_map[handle]
            hs = packet[1]
            data = bytearray.fromhex(hs)
            yield (uuid, handle, data)
