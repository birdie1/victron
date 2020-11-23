#!/usr/bin/env python
from victron_gatt import (
    get_device_instance,
    send_init_sequence,
    smart_shunt_ids,
    subscribe_notifications,
)
import gatt
from gatt.gatt_linux import Characteristic
import threading
import os
import sys
import time
from datetime import datetime, timedelta
import ipdb

############################ wireshark
# 1.)mkfifo /tmp/hci_dump.pcap
# 2.) nc -k -l  9000 >> dump_new_init.pcap
# 3.) hcidump -R -w /tmp/hci_dump.pcap
# 4.)nc 192.168.3.119 9000  < /tmp/hci_dump.pcap

######python convert values
# binascii.hexlify(struct.pack('<h',10*60))
# struct.unpack('>f',b'\x03\x84')

# original start of values sequence
VALUE_PREFIX = bytes.fromhex("08031903")


from enum import IntEnum


class VALUE_TYPES(IntEnum):
    FIXED_LEN = 0x09
    VAR_LEN = 0x08


class CATEGORY_TYPES(IntEnum):
    HISTORY = 0x03
    SETTINGS = 0x10
    VALUES = 0xED
    SETTINGS2 = 0x0F


TYPE_NAMES = {
    0x1: "unknown",
    0x2: "unknown",
    0x4: "single value reply",
    0x8: "unknown",
}

DATA_NAMES = {
    0x7D: "Starter",
    0x8C: "Current",
    0x8D: "Voltage",
    0x8E: "Power",
    0x8F: "Capacity",
    0xFE: "Capa (alt)??",
}

CATEGORY_NAMES = {
    0x03190308: "history values",
    0x03190309: "history bools",
    0x10190308: "settings values",
    0x10190309: "settings bools",
    0xED190308: "values values",
    0xED190309: "values bools",
    0x0F190308: "mixed settings",
}


MIXED_SETTINGS_NAMES = {
    0xFF: "Battery Charge Status",
}


HISTORY_VALUE_NAMES = {
    0x09: "hist synchronizations",
    0x03: "hist total caharge cycles",
    0x04: "hist full discharges",
}
HISTORY_VALUE_FUNS = {}

FIXEDLEN_CATEGORY_LOOKUP = {
    0x03190308: ("history values", HISTORY_VALUE_NAMES, None),
    0x03190309: "history bools",
    0x10190308: "settings values",
    0x10190309: "settings bools",
    0xED190308: "values values",
    0xED190309: "values bools",
    0x0F190308: "mixed settings",
}


def twos_comp(val, bits):
    """compute the 2's complement of int value val"""
    if (val & (1 << (bits - 1))) != 0:  # if sign bit is set e.g., 8bit: 128-255
        val = val - (1 << bits)  # compute negative value
    return val  # return positive value as is


def format_value_data(type_id, value):
    if type_id == 0x7D:
        converted = int.from_bytes(value, "little", signed=True)
        return str(converted / 100) + "V"
    if type_id == 0x8C:
        converted = int.from_bytes(value, "little", signed=True)
        return str(converted / 1000) + "A"
    if type_id == 0x8D:
        converted = int.from_bytes(value, "little", signed=False)
        return str(converted / 100) + "V"
    if type_id == 0x8E:
        converted = int.from_bytes(value, "little", signed=True)
        return str(converted) + "W"
    if type_id == 0x8F:
        converted = int.from_bytes(value, "little", signed=False)
        percent = converted / 0xFFFF * 100
        return str(percent) + "%"
    if type_id == 0xFE:
        converted = int.from_bytes(value, "little", signed=False)
        percent = converted / 0xFFFF * 100
        return str(percent) + "%"

    # else unknown
    converted = int.from_bytes(value, "little", signed=False)
    return converted


def format_mixed_settings(type_id, value):
    if type_id == 0xFF:
        converted = int.from_bytes(value, "little", signed=False)
        return str(converted / 100) + "%"


def get_label(data_type, data_name):
    try:
        return data_name[data_type]
    except:
        return f"unknown type (0x{data_type:0X})"


MIXED_SETTINGS_FUNS = {
    0xFF: format_mixed_settings,
}

VALUE_FUNS = {
    0x8C: format_value_data,
    0x8D: format_value_data,
    0x8E: format_value_data,
    0x7D: format_value_data,
}

VALUE_NAMES = {
    0x8C: "Current",
    0x8D: "Voltage",
    0x8E: "Power",
    0x7D: "Starter",
}

SETTINGS_NAMES = {
    0x00: "set capacity",
    0x01: "set charged voltage",
    0x02: "set tail current",
    0x03: "set charged detection time",
    0x04: "set charge eff. factor",
    0x05: "set peukert coefficient",
    0x06: "set current threshold",
    0x07: "set time-to-go avg. per.",
    0x08: "set discharge floor",
}

SETTINGS_FUNS = {
    0x00: format_value_data,
    0x01: format_value_data,
    0x02: format_value_data,
    0x03: format_value_data,
    0x04: format_value_data,
    0x05: format_value_data,
    0x06: format_value_data,
    0x07: format_value_data,
    0x08: format_value_data,
}
VARLEN_CATEGORY_LOOKUP = {
    0x03: ("history values", HISTORY_VALUE_NAMES, HISTORY_VALUE_FUNS),
    0x10: ("settings valu", SETTINGS_NAMES, SETTINGS_FUNS),
    0xED: ("values values", VALUE_NAMES, VALUE_FUNS),
    0x0F: ("mixed settings", MIXED_SETTINGS_NAMES, MIXED_SETTINGS_FUNS),
}


def decode_var_len(value, data_names, format_lookup):
    """function expects user data after 4-byte prefix
    bytes consumed start from data tpye
    """
    DATATYPE_POS = 0
    LENGHT_TYPE_POS = 1
    DATA_POS = 2

    length_type_field = value[LENGHT_TYPE_POS]
    length = length_type_field & 0x0F
    type_id = (length_type_field & 0xF0) >> 4
    data = value[DATA_POS : DATA_POS + length]

    data_type = value[DATATYPE_POS]
    data_label = get_label(data_type, data_names)

    format_fun = format_lookup[data_type]
    data_string = format_fun(data_type, data)
    consumed = 2 + length
    return f"{data_label}: {data_string}", consumed


def decode_fixed_len(value):
    """function expects whole packet with 4-byte prefix
    but counts consumed bytes without prefix!!
    """
    DATATYPE_POS = 0
    DATA_POS = 1

    data = value[DATA_POS]
    data_type = value[DATATYPE_POS]
    data_label = get_label(data_type, MIXED_SETTINGS_NAMES)
    data_string = format_mixed_settings(data_type, data)
    consumed = 2
    return f"{data_label}: {data_string}", consumed


import subprocess


def logger(text):
    print(text, file=sys.stderr)
    subprocess.run(
        ["/usr/bin/logger", f"--id={os.getpid()}", "-t", "Smard Schund", text]
    )


buffer = bytearray()


def signature_complete(value, signature):
    try:
        for pos, sig in signature:
            if not value[pos] == sig:
                return False
        return True
    except:
        return False


def start_of_packet(value):
    signature = [
        (1, 0x03),
        (2, 0x19),
    ]
    for offset, item in enumerate(value):
        if item == signature[0][1]:
            # slice from start of signature to end

            result = signature_complete(value[offset - signature[0][0] :], signature)
            if result == True:
                return offset - signature[0][0]
    return -1


from collections import namedtuple

Header = namedtuple("Header", ["value_type", "category_type", "length"])


def decode_header(header_4b):
    return Header(VALUE_TYPES(header_4b[0]), CATEGORY_TYPES(header_4b[3]), 4)


def handle_bulk_values(value):
    global buffer
    buffer.extend(value)

    pos = start_of_packet(buffer)
    while len(buffer) > 0 and pos >= 0:
        consumed = handle_one_value(buffer[pos:])
        buffer = buffer[pos + consumed :]
        pos = start_of_packet(buffer)
        if pos > 0 or pos < 0:  # TODO BUG: midnight hacking
            unknown = buffer[:pos]
            print(f"unknown value in bulk: {unknown}")


def handle_single_value(value):
    pos = start_of_packet(value)
    while pos >= 0:
        consumed = handle_one_value(value[pos:])
        value = value[pos + consumed :]
        pos = start_of_packet(value)
    if len(value) > 0:
        print(f"unknown single packet: {value}")


def handle_one_value(value):
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
        result, used = decode_var_len(value[consumed:], category[1], category[2])

    consumed += used
    logger(result)
    return consumed


UUID_HANDLER_TABLE = {
    smart_shunt_ids["0027"]: handle_bulk_values,
    smart_shunt_ids["0024"]: handle_single_value,
    smart_shunt_ids["0021"]: handle_single_value,
}

connect_timer = 5 * 60
disconnect_timer = 60
connect_retry_timer = 30
device = None


def connect_loop():
    global device
    print("connect")
    device.connect()
    time.sleep(5)
    if device.connected:
        next_time = datetime.now() + timedelta(seconds=disconnect_timer)
        logger(f"connected until {next_time:%H:%M:%S}")

        print("subscribe notifications")
        subscribe_notifications()

        print("send init seuqucene")
        send_init_sequence()
        # threading.Timer(disconnect_timer, disconnect_loop).start()
        return (disconnect_timer, disconnect_loop)
    else:
        next_time = datetime.now() + timedelta(seconds=connect_retry_timer)
        print(
            f"error connecting to device {device.mac_address}, retry at {next_time:%H:%M:%S}"
        )
        return (connect_retry_timer, connect_loop)
        # threading.Timer(connect_retry_timer, connect_loop).start()


def disconnect_loop():
    global device
    print("disconnect")
    device.disconnect()
    next_time = datetime.now() + timedelta(seconds=connect_timer)
    print(f"disconnected, connecting again at {next_time:%H:%M:%S} seconds")
    logger(f"connecting in {connect_timer}")
    return (connect_timer, connect_loop)
    # threading.Timer(connect_timer, connect_loop).start()


if __name__ == "__main__":

    # victron on its protocol
    # https://community.victronenergy.com/questions/40048/victron-data-capture-via-bluetooth.html

    print("prepare device")
    device = get_device_instance("fd:d4:50:0f:6c:1b", UUID_HANDLER_TABLE)
    print("connect now")
    next_state = (0, connect_loop)
    while True:
        time.sleep(next_state[0])
        next_state[1]()
    print("connect done")

    # print("manager run")
    # manager.run()
    # while True:
    #     time.sleep(20)
    #     send_ping()
