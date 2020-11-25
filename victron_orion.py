from os import name
from victron_gatt import AnyDevice, gatt_device_instance

# E7:79:E6:1D:EF:04 Orion
def init_sequence_template():
    stuff = [
        # very early, well-known endpoints.not needed for values
        #  ("000d":"0200"),
        #  ("001f":"0100"),
        ("001b", "fa80ff"),
        ("001b", "f980"),
        ("001e", "01"),
        ("001e", "0300"),
        ("001e", "0600821893421027"),
        ("001e", "050081190109"),
        ("0021", "05008119010a05008119ec0f05008119ec0e0500"),
        ("0021", "8119221105008119221205008119222205008119"),
        ("0021", "222305008119ed8d05008119edbb050081190201"),
        ("001e", "05008119edda050081190207050081190205"),
        ("0021", "05008119edf105008119edf705008119edf60500"),
        ("0021", "8119edfc05008119edfe05008119edfb05008119"),
        ("0021", "edef05008119ed2e05008119ede905008119ee14"),
        ("001e", "05008119ee15050081190320050081190321"),
        ("0021", "05008119020605008119020005008119ee360500"),
        ("0021", "8119ee3705008119ee3805008119ee3905008119"),
        ("0021", "0150050081189005008118910500810405008119"),
        ("001e", "ec3f05008119ec12"),
        # 16 sec
        ("001b", "f941"),
        # 16sec
        ("001e", "0600821902064101"),
        # 4.5sec
        ("001e", "0600821902064100"),
        # 12sec
        ("001e", "050081190101"),
        ("001e", "050081190105"),
        # 1sec
        ("001b", "f941"),
        ########### END copied from wireshark
    ]
    for packet in stuff:
        handle = packet[0]
        uuid = handle_uuid_map[handle]
        hs = packet[1]
        data = bytearray.fromhex(hs)
        yield (uuid, handle, data)


ping = [
    ("0024", "0300"),
    ("0021", "f941"),  # taken from phoenix, sends power & current
]

handle_uuid_map = {
    # [NEW] Primary Service (Handle 0x9abd)
    # 	/org/bluez/hci0/dev_E7_79_E6_1D_EF_04/service000a
    # 	00001801-0000-1000-8000-00805f9b34fb
    # 	Generic Attribute Profile
    # [NEW] Characteristic (Handle 0x68ab)
    # 	/org/bluez/hci0/dev_E7_79_E6_1D_EF_04/service000a/char000b
    # 	00002a05-0000-1000-8000-00805f9b34fb
    # 	Service Changed
    "000c": "00002a05-0000-1000-8000-00805f9b34fb",
    # [NEW] Descriptor (Handle 0x2400)
    # 	/org/bluez/hci0/dev_E7_79_E6_1D_EF_04/service000a/char000b/desc000d
    # 	00002902-0000-1000-8000-00805f9b34fb
    # 	Client Characteristic Configuration
    # [NEW] Primary Service (Handle 0x9abd)
    # 	/org/bluez/hci0/dev_E7_79_E6_1D_EF_04/service000e
    # 	97580001-ddf1-48be-b73e-182664615d8e
    # 	Vendor specific
    # [NEW] Characteristic (Handle 0x68ab)
    # 	/org/bluez/hci0/dev_E7_79_E6_1D_EF_04/service000e/char000f
    # 	97580002-ddf1-48be-b73e-182664615d8e
    # 	Vendor specific
    "0010": "97580002-ddf1-48be-b73e-182664615d8e",
    # [NEW] Characteristic (Handle 0x68ab)
    # 	/org/bluez/hci0/dev_E7_79_E6_1D_EF_04/service000e/char0011
    # 	97580003-ddf1-48be-b73e-182664615d8e
    # 	Vendor specific
    "0012": "97580003-ddf1-48be-b73e-182664615d8e",
    # [NEW] Descriptor (Handle 0x20c0)
    # 	/org/bluez/hci0/dev_E7_79_E6_1D_EF_04/service000e/char0011/desc0013
    # 	00002902-0000-1000-8000-00805f9b34fb
    # 	Client Characteristic Configuration
    # [NEW] Characteristic (Handle 0x68ab)
    # 	/org/bluez/hci0/dev_E7_79_E6_1D_EF_04/service000e/char0014
    # 	97580004-ddf1-48be-b73e-182664615d8e
    # 	Vendor specific
    "0015": "97580004-ddf1-48be-b73e-182664615d8e",
    # [NEW] Characteristic (Handle 0x68ab)
    # 	/org/bluez/hci0/dev_E7_79_E6_1D_EF_04/service000e/char0016
    # 	97580006-ddf1-48be-b73e-182664615d8e
    # 	Vendor specific
    "0016": "97580006-ddf1-48be-b73e-182664615d8e",
    # [NEW] Descriptor (Handle 0x2000)
    # 	/org/bluez/hci0/dev_E7_79_E6_1D_EF_04/service000e/char0016/desc0018
    # 	00002902-0000-1000-8000-00805f9b34fb
    # 	Client Characteristic Configuration
    # [NEW] Primary Service (Handle 0x9abd)
    # 	/org/bluez/hci0/dev_E7_79_E6_1D_EF_04/service0019
    # 	306b0001-b081-4037-83dc-e59fcc3cdfd0
    # 	Vendor specific
    # [NEW] Characteristic (Handle 0x68ab)
    # 	/org/bluez/hci0/dev_E7_79_E6_1D_EF_04/service0019/char001a
    # 	306b0002-b081-4037-83dc-e59fcc3cdfd0
    # 	Vendor specific
    "001b": "306b0002-b081-4037-83dc-e59fcc3cdfd0",
    # [NEW] Descriptor (Handle 0xf100)
    # 	/org/bluez/hci0/dev_E7_79_E6_1D_EF_04/service0019/char001a/desc001c
    # 	00002902-0000-1000-8000-00805f9b34fb
    # 	Client Characteristic Configuration
    # [NEW] Characteristic (Handle 0x68ab)
    # 	/org/bluez/hci0/dev_E7_79_E6_1D_EF_04/service0019/char001d
    # 	306b0003-b081-4037-83dc-e59fcc3cdfd0
    "001e": "306b0003-b081-4037-83dc-e59fcc3cdfd0",
    # 	Vendor specific
    # [NEW] Descriptor (Handle 0xf0c0)
    # 	/org/bluez/hci0/dev_E7_79_E6_1D_EF_04/service0019/char001d/desc001f
    # 	00002902-0000-1000-8000-00805f9b34fb
    # 	Client Characteristic Configuration
    "001e": "00002902-0000-1000-8000-00805f9b34fb",
    # [NEW] Characteristic (Handle 0x68ab)
    # 	/org/bluez/hci0/dev_E7_79_E6_1D_EF_04/service0019/char0020
    # 	306b0004-b081-4037-83dc-e59fcc3cdfd0
    # 	Vendor specific
    "0021": "306b0004-b081-4037-83dc-e59fcc3cdfd0",
    # [NEW] Descriptor (Handle 0xc080)
    # 	/org/bluez/hci0/dev_E7_79_E6_1D_EF_04/service0019/char0020/desc0022
    # 	00002902-0000-1000-8000-00805f9b34fb
    # 	Client Characteristic Configuration
    # [NEW] Primary Service (Handle 0x9abd)
    # 	/org/bluez/hci0/dev_E7_79_E6_1D_EF_04/service0023
    # 	306b0001-b081-4037-83dc-e59fcc3cdfd1
    # 	Vendor specific
    # [NEW] Characteristic (Handle 0x68ab)
    # 	/org/bluez/hci0/dev_E7_79_E6_1D_EF_04/service0023/char0024
    # 	306b0002-b081-4037-83dc-e59fcc3cdfd1
    # 	Vendor specific
    "0025": "306b0002-b081-4037-83dc-e59fcc3cdfd1",
    # [NEW] Descriptor (Handle 0xf020)
    # 	/org/bluez/hci0/dev_E7_79_E6_1D_EF_04/service0023/char0024/desc0026
    # 	00002902-0000-1000-8000-00805f9b34fb
    # 	Client Characteristic Configuration
    # [NEW] Characteristic (Handle 0x68ab)
    # 	/org/bluez/hci0/dev_E7_79_E6_1D_EF_04/service0023/char0027
    # 	306b0003-b081-4037-83dc-e59fcc3cdfd1
    # 	Vendor specific
    "0028": "306b0003-b081-4037-83dc-e59fcc3cdfd1",
    # [NEW] Descriptor (Handle 0x24c0)
    # 	/org/bluez/hci0/dev_E7_79_E6_1D_EF_04/service0023/char0027/desc0029
    # 	00002902-0000-1000-8000-00805f9b34fb
    # 	Client Characteristic Configuration
    # [NEW] Characteristic (Handle 0x68ab)
    # 	/org/bluez/hci0/dev_E7_79_E6_1D_EF_04/service0023/char002a
    # 	306b0004-b081-4037-83dc-e59fcc3cdfd1
    # 	Vendor specific
    "002b": "306b0004-b081-4037-83dc-e59fcc3cdfd1",
    # [NEW] Descriptor (Handle 0x2800)
    # 	/org/bluez/hci0/dev_E7_79_E6_1D_EF_04/service0023/char002a/desc002c
    # 	00002902-0000-1000-8000-00805f9b34fb
    # 	Client Characteristic Configuratio
}


def get_device_instance(mac, name, handle_single_value, handle_bulk_values):
    UUID_FUNCTION_TABLE = {
        handle_uuid_map["0025"]: handle_single_value,
        handle_uuid_map["001b"]: handle_single_value,
        handle_uuid_map["000c"]: handle_single_value,
        handle_uuid_map["001e"]: handle_single_value,
        handle_uuid_map["0021"]: handle_bulk_values,
    }

    return gatt_device_instance(
        mac,
        notification_table=UUID_FUNCTION_TABLE,
        ping=ping,
        handle_uuid_map=handle_uuid_map,
        name=name,
        init_sequence_template=init_sequence_template,
    )