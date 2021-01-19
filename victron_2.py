#!/usr/bin/env python3
import argparse
import logging
import traceback
import os
import re
import subprocess
import sys
import threading
import time
import yaml
from collections import namedtuple
from datetime import datetime, timedelta
from enum import IntEnum
from time import sleep

import ipdb

import victron_gatt
import victron_orion
import victron_smartshunt
import victron_smartsolar


with open("config.yml", 'r') as ymlfile:
    config = yaml.full_load(ymlfile)


logger_format = '[%(levelname)-7s] (%(asctime)s) %(filename)s::%(lineno)d %(message)s'
logging.basicConfig(level=logging.DEBUG,
                    format=logger_format,
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename=f"main.log")
logger = logging.getLogger()

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter(logger_format)
handler.setFormatter(formatter)
logger.addHandler(handler)


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
    output_mqtt(device_name, result)
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
    output_mqtt(device_name, result)
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


def connect_loop(device):
    logger.info(f"{device.name}: connecting...")
    try:
        device.connect()
    except:
        logger.error(f"{device.name}: failed to connect. Trying again shortly.")
        return False
    # maybe important. sleep(0) yields to other threads - give eventloop a chance to work
    time.sleep(0)
    logger.info(f"{device.name}: connected: {device.connected}")
    if device.connected:
        device.subscribe_notifications()
        time.sleep(2)
        print(f"{device.name} send init sequence")
        device.start_send_init_squence()
        return True
    else:
        logger.error(f"{device.name}: failed to connect. Trying again shortly.")
        return False


def disconnect_loop(device):
    logger.info(f"{device.name}: disconnecting: Planned by connect_timer")
    device.disconnect()
    return connect_loop


def connect_disconnect_loop(devices):
    next_state = (0, connect_loop)
    i = 0
    while True:
        try:
            if connect_loop(devices[i]):
                next_time = datetime.now() + timedelta(seconds=config['timer']['connected'])

                logger.info(f"{devices[i].name}: BT connected until {next_time:%H:%M:%S}")
                output_mqtt(devices[i].name, f"BT connected until {next_time:%H:%M:%S}")

                sleep(config['timer']['connected'])

                disconnect_loop(devices[i])
            else:
                logger.info(f'{devices[i].name}: Reconnecting in {config["timer"]["retry"]}')
                sleep(config["timer"]["retry"])
        except:
            # catch all to keep thread going
            traceback.print_stack()
        sleep(2)
        i = (i + 1) % len(devices)


def prepare_device(device):
    logger.info(f"{device['name']} preparing...")

    if device['type'] == 'smartshunt':
        device = victron_smartshunt.get_device_instance(device['mac'], device['name'], handle_single_value, handle_bulk_values)
    elif device['type'] == 'smartsolar':
        device = victron_smartsolar.get_device_instance(device['mac'], device['name'], handle_single_value, handle_bulk_values)
    elif device['type'] == 'orionsmart':
        device = victron_orion.get_device_instance(device['mac'], device['name'], handle_single_value, handle_bulk_values)

    return device


def get_helper_string_device(devices):
    return_string = ""
    for count, device in enumerate(devices):
        return_string += f"{count}: {device['name']} | "
    return return_string


def output_sys(device, text):
    print(f"{device}:{text}", file=sys.stderr)
    subprocess.run(
        [
            "/usr/bin/logger",
            f"--id={os.getpid()}",
            "-t",
            "victron",
            f"{device}:{text}",
        ]
    )


def output_mqtt(device, text):
    global client

    client.publish(f"victron/{device}", text)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Victron Reader (Bluetooth or Serial) \n\n"
                                                 "Current supported devices:\n"
                                                 "  Full: \n" 
                                                 "  Partial: \n"
                                                 "    - Smart Shunt (Bluetooth)\n"
                                                 "    - Smart Solar (Bluetooth)\n"
                                                 "    - Orion Smart (Bluetooth)\n"
                                                 "    - Phenoix Inverter (Serial)",
                                     formatter_class=argparse.RawTextHelpFormatter)
    group01 = parser.add_argument_group()
    group01.add_argument("--debug", action="store_true", help="Set log level to debug")
    group01.add_argument("--info", action="store_true", help="Set log level to info")
    group01.add_argument("--quiet", action="store_true", help="Set log level to error")

    group02 = parser.add_argument_group()
    group02.add_argument(
        "-p",
        "--print",
        metavar="",
        type=bool,
        help="Print only one time and exit",
        required=False,
    )

    group03 = parser.add_argument_group()
    group03.add_argument(
        "-d",
        "--device",
        metavar="NUM",
        type=int,
        help=get_helper_string_device(config['devices']),
        required=False,
    )
    args = parser.parse_args()

    if config['logger'] == 'mqtt':
        import paho.mqtt.client as mqtt

        client = mqtt.Client()
        client.connect(config['mqtt']['host'], config['mqtt']['port'], 60)
        client.loop_start()

    if args.device is not None:
        if config['devices'][args.device]['protocol'] == 'bluetooth':
            devices = [prepare_device(config['devices'][args.device])]
            t1 = threading.Timer(0, connect_disconnect_loop, args=(devices,))
        elif config['devices'][args.device]['protocol'] == 'serial':
            print(f'{config["devices"][args.device]["name"]}: SERIAL COMMUNICATION NOT IMPLEMENTED')
    else:
        for count, device in enumerate(config['devices']):
            devices = []

            if config['devices'][args.device]['protocol'] == 'bluetooth':
                devices.append(prepare_device(device))
            elif config['devices'][args.device]['protocol'] == 'serial':
                print(f'{device["name"]}: SERIAL COMMUNICATION NOT IMPLEMENTED')

            t1 = threading.Timer(0, connect_disconnect_loop, args=(devices,))

    t1.start()

    logger.info("Gatt manager event loop starting...")
    victron_gatt.manager.run()
