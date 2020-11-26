#!/usr/bin/env python
import argparse
import os
import re
import subprocess
import sys
import threading
import time
from collections import namedtuple
from datetime import datetime, timedelta
from enum import IntEnum

import ipdb

import victron_gatt
import victron_orion
import victron_smartshunt
import victron_smartsolar

# victron on its protocol
# https://community.victronenergy.com/questions/40048/victron-data-capture-via-bluetooth.html

############################ wireshark
# 1.)mkfifo /tmp/hci_dump.pcap
# 2.) nc -k -l  9000 >> dump_new_init.pcap
# 3.) hcidump -R -w /tmp/hci_dump.pcap
# 4.)nc 192.168.3.119 9000  < /tmp/hci_dump.pcap

######python convert values
# binascii.hexlify(struct.pack('<h',10*60))
# struct.unpack('>f',b'\x03\x84')

####### howto get handle->uuid map
# use bluetoothctl, connect device
# in characteristic enumeration:
# find "Characteristic" entry
# take uuid, take "char" + 1
# Example:
# [NEW] Characteristic
#        /org/bluez/hci0/dev_FD_D4_50_0F_6C_1B/service001f/char0020
#        306b0002-b081-4037-83dc-e59fcc3cdfd0
# handle: 0021, uuid:306b0002-b081-4037-83dc-e59fcc3cdfd0

# original start of values sequence
VALUE_PREFIX = bytes.fromhex("08031903")
Header = namedtuple("Header", ["value_type", "category_type", "length"])


class VALUE_TYPES(IntEnum):
    FIXED_LEN = 0x09
    VAR_LEN = 0x08


TYPE_NAMES = {
    0x1: "unknown",
    0x2: "unknown",
    0x4: "single value reply",
    0x8: "unknown",
}

FIXED_DATA_NAMES = {
    0x7D: ("FIXED Starter", 100, "V"),
    0x8C: ("FIXED Current", 1000, "A"),
    0x8D: ("FIXED Voltage", 100, "V"),
    0x8E: ("FIXED Power", 1, "W"),
    0x8F: ("FIXED Capacity", 100, "%"),
}


MIXED_SETTINGS_NAMES = {
    0xFF: ("Battery Charge Status", "%", 100, False),
}


HISTORY_VALUE_NAMES = {
    0x00: ("hist: deepest discharge", "Ah", 10, True),
    0x01: ("hist: last discharge", "Ah", 10, True),
    0x02: ("hist: Average Discharge", "Ah", 10, True),
    0x03: ("hist: total charge cycles", "", 1, False),
    0x04: ("hist: full discharges", "", 1, False),
    0x05: ("hist: Cumulative Ah drawn", "Ah", 10, True),
    0x06: ("hist: Min battery voltage", "V", 100, False),
    0x07: ("hist: Max battery voltage", "V", 100, False),
    0x08: ("hist: Time since last full", "sec", 1, True),
    0x09: ("hist: synchronizations", "", 1, False),
    0x10: ("hist: Discharged Energy", "Ah", 100, False),
    0x11: ("hist: Charged Energy", "Ah", 100, False),
}

SETTINGS_VALUE_NAMES = {
    0x00: ("set capacity", "Ah", 1, False),
    0x01: ("set charged voltage", "V", 1, False),
    0x02: ("set tail current", "A", 1, False),
    0x03: ("set charged detection time", "sec", 1, False),
    0x04: ("set charge eff. factor", "", 1, False),
    0x05: ("set peukert coefficient", "", 1, False),
    0x06: ("set current threshold", "%", 1, False),
    0x07: ("set time-to-go avg. per.", "sec", 1, False),
    0x08: ("set discharge floor", "V?", 1, False),
}


VALUE_VALUE_NAMES = {
    0x8C: ("Current", "A", 1000, True),
    0x8D: ("Voltage", "V", 100, False),
    0x8E: ("Power", "W", 1.0, True),
    0x7D: ("Starter", "V", 100, True),
    0x8F: ("SmartSolar Battery Current", "A", 10, True),
    0xBC: ("SmartSolar Power", "W", 100, True),
    0xBD: ("SmartSolar Solar Current", "A", 10, True),
    0xBB: ("SmartSolar Solar Voltage", "V", 100, True),
    0xEF: ("SmartSolar Setting Battery Voltage", "V", 1, True),
    0xF0: ("SmartSolar Setting Charge Current", "A", 1, True),
    0xF6: ("SmartSolar Setting Float Voltage", "V", 100, True),
}

ORION_SETTINGS_NAMES = {
    0x36: ("Orion Shutdown Voltage", "V", 100, True),
    0x37: ("Orion Start Voltage", "V", 100, True),
    0x38: ("Orion Delayed Start Voltage", "V", 100, True),
    0x39: ("Orion Start Delay", "sec", 1, True),
}

ORION_VALUE_NAMES = {
    0xBB: ("Orion Input Voltage", "V", 100, True),
    0xE9: ("Orion Set Delayed start voltage delay", "sec", 10, True),
}
VARLEN_CATEGORY_LOOKUP = {
    0x03190308: ("history values", HISTORY_VALUE_NAMES),
    0x10190308: ("settings valu", SETTINGS_VALUE_NAMES),
    0xED190308: ("values values", VALUE_VALUE_NAMES),
    0x0F190308: ("mixed settings", MIXED_SETTINGS_NAMES),
    0x01190008: ("Orion Values UKNNOWN", ORION_VALUE_NAMES),
    0xEC190008: ("streaming smartshunt UNKKNOWN", VALUE_VALUE_NAMES),
    0xED190008: ("Orion Values", ORION_VALUE_NAMES),
    0xEE190008: ("Orion Settings", ORION_SETTINGS_NAMES),
}


FIXEDLEN_CATEGORY_LOOKUP = {
    0x03190308: ("history values", HISTORY_VALUE_NAMES, None),
    0x03190309: "history bools",
    0x10190308: "settings values",
    0x10190309: "settings bools",
    0xED190308: ("values values", FIXED_DATA_NAMES, None),
    0xED190309: "values bools",
    0x0F190308: "mixed settings",
}


SIGNATURE = [
    (1, (0x03, 0x00)),
    (2, (0x19,)),
]


def twos_comp(val, bits):
    """compute the 2's complement of int value val"""
    if (val & (1 << (bits - 1))) != 0:  # if sign bit is set e.g., 8bit: 128-255
        val = val - (1 << bits)  # compute negative value
    return val  # return positive value as is


def logger(text):
    print(text, file=sys.stderr)
    subprocess.run(
        [
            "/usr/bin/logger",
            f"--id={os.getpid()}",
            "-t",
            "victron",
            text,
        ]
    )


def format_value(value, config):
    converted = int.from_bytes(value, "little", signed=config[3])
    return str(converted / config[2]) + config[1]


def get_label(command, command_names):
    try:
        return command_names[command][0]
    except:
        return f"unknown type (0x{command:0X})"


def signature_complete(value, signature):
    try:
        for pos, sigs in signature:
            if not value[pos] in sigs:
                return False
        return True
    except:
        return False


def start_of_packet(value):
    for offset, _ in enumerate(value):
        # slice from start of signature to end
        result = signature_complete(value[offset:], SIGNATURE)
        if result == True:
            return offset
    return -1


def decode_header(header_4b):
    return Header(VALUE_TYPES(header_4b[0]), int.from_bytes(bytes(header_4b[:4]), "little"), 4)


def decode_var_len(value, config_table):
    COMMAND_POS = 0
    LENGHT_TYPE_POS = 1
    DATA_POS = 2

    length_type_field = value[LENGHT_TYPE_POS]
    length = length_type_field & 0x0F
    type_id = (length_type_field & 0xF0) >> 4
    data = value[DATA_POS : DATA_POS + length]

    command = value[COMMAND_POS]
    if command not in config_table:
        raise KeyError(f"unknown command 0x{command:x}")

    data_label = get_label(command, config_table)
    config = config_table[command]
    data_string = format_value(data, config)

    consumed = 2 + length
    return f"{data_label}: {data_string}", consumed


def handle_one_value(value, device_name):
    header = decode_header(value)

    if (
        header.value_type == VALUE_TYPES.FIXED_LEN
        and len(value) < 6
        or header.value_type == VALUE_TYPES.VAR_LEN
        and len(value) < 6
    ):
        return -1

    result = ""
    consumed = header.length
    used = 0

    if header.value_type == VALUE_TYPES.FIXED_LEN:
        result, used = decode_fixed_len(value[consumed:], header)
    if header.value_type == VALUE_TYPES.VAR_LEN:
        category = VARLEN_CATEGORY_LOOKUP[header.category_type]
        result, used = decode_var_len(value[consumed:], category[1])

    consumed += used
    logger(f"{device_name}: {result}")
    return consumed


def decode_fixed_len(value):
    """function expects whole packet with 4-byte prefix"""
    DATATYPE_POS = 0
    DATA_POS = 1

    data = value[DATA_POS]
    data_type = value[DATATYPE_POS]
    data_label = get_label(data_type, MIXED_SETTINGS_NAMES)
    data_string = format_value(data_type, data)
    consumed = 2
    return f"{data_label}: {data_string}", consumed


def handle_one_value(value, device_name):
    header = decode_header(value)

    if (
        header.value_type == VALUE_TYPES.FIXED_LEN
        and len(value) < 6
        or header.value_type == VALUE_TYPES.VAR_LEN
        and len(value) < 6
    ):
        return -1

    result = ""
    consumed = header.length
    used = 0

    if header.value_type == VALUE_TYPES.FIXED_LEN:
        result, used = decode_fixed_len(value[consumed:], header)
    if header.value_type == VALUE_TYPES.VAR_LEN:
        category = VARLEN_CATEGORY_LOOKUP[header.category_type]
        result, used = decode_var_len(value[consumed:], category[1])

    consumed += used
    logger(f"{device_name}: {result}")
    return consumed


buffer = bytearray()


def handle_bulk_values(value, device_name):
    global buffer
    buffer.extend(value)

    pos = start_of_packet(buffer)
    while len(buffer) > 0 and pos >= 0:
        consumed = handle_one_value(buffer[pos:], device_name)
        buffer = buffer[pos + consumed :]
        pos = start_of_packet(buffer)
        if pos > 0:  # TODO BUG: midnight hacking
            unknown = buffer[:pos]
            print(f"{device_name}: unknown value in bulk: {unknown}")
        if consumed == -1:
            print("{device_name}: bulk: need more bytes")
            return


def handle_single_value(value, device_name):

    pos = start_of_packet(value)
    while pos >= 0:
        consumed = handle_one_value(value[pos:], device_name)
        value = value[pos + consumed :]
        pos = start_of_packet(value)
    if len(value) > 0:
        print(f"{device_name}: unknown single packet: {value}")


connect_timer = 30  # during dev. for prod: 5 * 60
disconnect_timer = 60
connect_retry_timer = 30
device = None


def connect_loop(device):
    print(f"{device.name} connect")
    try:
        device.connect()
    except:
        next_time = datetime.now() + timedelta(seconds=connect_retry_timer)
        logger(f"{device.name} BT error connecting retry at {next_time:%H:%M:%S}")
        return (connect_retry_timer, connect_loop)
    # maybe important. sleep(0) yields to other threads - give eventloop a chance to work
    time.sleep(0)
    print(f"{device.name} connected:{device.connected}")
    if device.connected:
        next_time = datetime.now() + timedelta(seconds=disconnect_timer)
        logger(f"{device.name} BT connected until {next_time:%H:%M:%S}")

        device.subscribe_notifications()
        time.sleep(2)
        print(f"{device.name} send init sequence")
        device.start_send_init_squence()
        time.sleep(20)
        return (disconnect_timer, disconnect_loop)
    else:
        next_time = datetime.now() + timedelta(seconds=connect_retry_timer)
        print(
            f"{device.name} error connecting to device {device.mac_address}, retry at {next_time:%H:%M:%S}"
        )
        logger(f"{device.name} BT error connecting retry at {next_time:%H:%M:%S}")
        return (connect_retry_timer, connect_loop)


def disconnect_loop(device):
    print(f"{device.name} planned disconnect")
    device.disconnect()
    next_time = datetime.now() + timedelta(seconds=connect_timer)
    logger(f"{device.name} BT disconnected, connecting again at {next_time:%H:%M:%S}")
    print(f"{device.name} connecting in {connect_timer}")
    return (connect_timer, connect_loop)


def connect_disconnect_loop(device):
    print(f"{device.name} start timer loop")
    next_state = (0, connect_loop)
    while True:
        time.sleep(next_state[0])
        next_state = next_state[1](device)


def prepare_device(device, start_delay):
    device_fun = device[0]
    mac = device[1]
    name = device[2]

    print(f"prepare device {name}")
    device = device_fun(mac, name, handle_single_value, handle_bulk_values)
    t1 = threading.Timer(start_delay, connect_disconnect_loop, args=(device,))
    t1.start()


# F9:8E:1C:EC:9C:72 SmartSolar HQ2027LDKCU
# E7:79:E6:1D:EF:04 Orion
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="victron BT reader")
    parser.add_argument(
        "-d",
        "--device",
        metavar="NUM",
        type=int,
        help="1: smartshunt, 2: smartsolar, 3:orion",
        required=False,
    )
    args = parser.parse_args()

    DEVICES = [
        (victron_smartshunt.get_device_instance, "fd:d4:50:0f:6c:1b", "SmartdSchund"),
        (victron_smartsolar.get_device_instance, "F9:8E:1C:EC:9C:72", "SmartSolar"),
        (victron_orion.get_device_instance, "E7:79:E6:1D:EF:04", "Orion"),
    ]
    print(f"starting with devices: {args.device}")
    if args.device:  # 0 equals false :(
        prepare_device(DEVICES[args.device - 1], 0)
    else:
        for i, device in enumerate(DEVICES):
            prepare_device(device, i * 10)
    print("manager event loop startinf")
    victron_gatt.manager.run()