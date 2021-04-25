#!/usr/bin/env python3
import argparse
import copy
import faulthandler
import json
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
import victron_phoenix

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


#MIXED_SETTINGS_NAMES = {
#    0xFF: ("Battery", "Charge Status", "%", 100, False),
#}

def extract_firmware_version(value):
    if value == b'\xff\xff\xff':
        return 'NO FIRMWARE'
    if value[2] != 0:
        version = f'v{value[2]}{value[1]:02}.{value[0]:02}'
    else:
        version = f'v{value[1]}.{value[0]:02}'
    return version

def convert_value_number(value, command):
    converted = int.from_bytes(value, "little", signed=command[4])
    return str(converted / command[3])

def convert_value_int(value, command):
    converted = int.from_bytes(value, "little", signed=command[4])
    return str(int(converted / command[3]))

def convert_value_string(value, command):
    return str(value.decode("ASCII"))

def convert_value_firmware(value, command):
    return extract_firmware_version(value[1:])

def convert_value_udf(value, command):
    return extract_firmware_version(value[0:3])

def convert_value_identify(value, command):
    if int.from_bytes(value, "little") == 0:
        return "normal operation (default)"
    else:
        return "identification mode (blink/beep)"
def convert_value_unknown(value, command):
    return str(value)


# VALUE ARRAY
# HEX VALUE -> (Type, Description, devider, signed, converter)
# 0x??: ("Battery", "Time to go", "min", 1, False, convert_value_number),

MIXED_SETTINGS_NAMES = {
    0xFE: ("Battery", "Time to go", "min", 1, False, convert_value_int),
    0xFF: ("Battery", "Charge Status", "%", 100, False, convert_value_number),
}

HISTORY_VALUE_NAMES = {
    0x00: ("History", "Deepest Discharge", "Ah", 10, True, convert_value_number),
    0x01: ("History", "Last Discharge", "Ah", 10, True, convert_value_number),
    0x02: ("History", "Average Discharge", "Ah", 10, True, convert_value_number),
    0x03: ("History", "Total Charge Cycles", "", 1, False, convert_value_number),
    0x04: ("History", "Full Discharges", "", 1, False, convert_value_number),
    0x05: ("History", "Cumulative Ah Drawn", "Ah", 10, True, convert_value_number),
    0x06: ("History", "Min Battery Voltage", "V", 100, False, convert_value_number),
    0x07: ("History", "Max Battery Voltage", "V", 100, False, convert_value_number),
    0x08: ("History", "Time Since Last Full", "sec", 1, True, convert_value_int),
    0x09: ("History", "Synchronizations", "", 1, False, convert_value_number),
    0x10: ("History", "Discharged Energy", "Ah", 100, False, convert_value_number),
    0x11: ("History", "Charged Energy", "Ah", 100, False, convert_value_number),
}

SETTINGS_AND_SOLAR_HISTORY_VALUE_NAMES = {
    0x00: ("Settings", "Capacity", "Ah", 1, False, convert_value_number),
    0x01: ("Settings", "Charged Voltage", "V", 1, False, convert_value_number),
    0x02: ("Settings", "Tail Current", "A", 1, False, convert_value_number),
    0x03: ("Settings", "Charged Detection Time", "sec", 1, False, convert_value_number),
    0x04: ("Settings", "Charge effectic factor", "", 1, False, convert_value_number),
    0x05: ("Settings", "Peukert Coefficient", "", 1, False, convert_value_number),
    0x06: ("Settings", "Current Threshold", "%", 1, False, convert_value_number),
    0x07: ("Settings", "Time-to-go avg. per.", "sec", 1, False, convert_value_number),
    0x08: ("Settings", "Discharge Floor", "V?", 1, False, convert_value_number),
}


VALUE_VALUE_NAMES = {
    0x8C: ("Latest", "Current", "A", 1000, True, convert_value_number),
    0x8D: ("Latest", "Voltage", "V", 100, False, convert_value_number),
    0x8E: ("Latest", "Power", "W", 1.0, True, convert_value_number),
    0x7D: ("Latest", "Starter", "V", 100, True, convert_value_number),
    0x8F: ("Latest", "SmartSolar Battery Current", "A", 10, True, convert_value_number),
    0xBC: ("Latest", "SmartSolar Power", "W", 100, True, convert_value_number),
    0xBD: ("Latest", "SmartSolar Solar Current", "A", 10, True, convert_value_number),
    0xBB: ("Latest", "SmartSolar Solar Voltage", "V", 100, True, convert_value_number),
    0xEF: ("Latest", "SmartSolar Setting Battery Voltage", "V", 1, True, convert_value_number),
    0xF0: ("Latest", "SmartSolar Setting Charge Current", "A", 1, True, convert_value_number),
    0xF6: ("Latest", "SmartSolar Setting Float Voltage", "V", 100, True, convert_value_number),
}

ORION_SETTINGS_NAMES = {
    0x36: ("Settings", "Shutdown Voltage", "V", 100, True, convert_value_number),
    0x37: ("Settings", "Start Voltage", "V", 100, True, convert_value_number),
    0x38: ("Settings", "Delayed Start Voltage", "V", 100, True, convert_value_number),
    0x39: ("Settings", "Orion Start Delay", "sec", 1, True, convert_value_number),
}

ORION_VALUE_NAMES = {
    0xBB: ("Latest", "Input Voltage", "V", 100, True, convert_value_number),
    0xE9: ("Settings", "Delayed start voltage delay", "sec", 10, True, convert_value_number),
}

## Found in PDF: VE.Can registers
PRODUCT_INFO_NAMES = {
    0x00: ("Product", "ID", "", 1, True, convert_value_unknown),
    0x01: ("Product", "Revision", "", 1, True, convert_value_unknown),
    0x02: ("Product", "Firmware Version", "", 1, True, convert_value_firmware),
    0x03: ("Product", "Minimum Firmware Version", "", 1, True, convert_value_unknown),
    0x04: ("Product", "GroupID", "", 1, True, convert_value_unknown),
    0x05: ("Product", "Hardware Revision", "", 1, True, convert_value_unknown),
    0x0A: ("Product", "Serial", "", 1, True, convert_value_string),
    0x0B: ("Product", "Model Name", "", 1, True, convert_value_unknown),
    0x0C: ("Product", "Installation description 1", "", 1, True, convert_value_unknown),
    0x0D: ("Product", "Installation description 2", "", 1, True, convert_value_unknown),
    0x0E: ("Product", "Identify", "", 1, True, convert_value_identify),
    0x10: ("Product", "Udf version", "", 1, True, convert_value_udf),
    0x20: ("Product", "Uptime", "", 1, True, convert_value_unknown),
    0x40: ("Product", "Capabilities (NOT DECODED, See PDF Ve.Direct Protocol)", "", 1, True, convert_value_unknown),
}

# Category lookup
# Description: Lookup base command
#       0x01190308 -> 0x01 you will find in the description pdfs from victron for other buses, like ve.direct or ve.can
#
# HEX VALUE -> (Description, value array, converter)
# 0x??: ("Battery", "Time to go", "min", 1, False),
VARLEN_CATEGORY_LOOKUP = {
    0x01190308: ("Product Info", PRODUCT_INFO_NAMES),
    0x03190308: ("history values", HISTORY_VALUE_NAMES),
    0x10190308: ("settings valu", SETTINGS_AND_SOLAR_HISTORY_VALUE_NAMES),
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

SOLAR_HISTORY_VALUES = [
    (12, 2, ("History", "Battery Voltage Max", "V", 100, True)),
    (14, 2, ("History", "Battery Voltage Min", "V", 100, True)),
    (21, 2, ("History", "Total Work", "kWh", 100, False)),
    (27, 1, ("History", "Solar Power Max", "W", 1, False)),
    (33, 2, ("History", "Solar Voltage Max", "V", 100, True)),
    # array always is 36bytes
]


## for decode_var_len()
COMMAND_POS = 0
LENGHT_TYPE_POS = 1
DATA_POS = 2
HISTORY_MIN_CMD = 0x50
HISTORY_MAX_CMD = HISTORY_MIN_CMD + 31




def twos_comp(val, bits):
    """compute the 2's complement of int value val"""
    if (val & (1 << (bits - 1))) != 0:  # if sign bit is set e.g., 8bit: 128-255
        val = val - (1 << bits)  # compute negative value
    return val  # return positive value as is


def format_value(value, config):
    converted = int.from_bytes(value, "little", signed=config[4])
    return str(converted / config[3]) + config[2]


def get_label(command, command_names):
    try:
        return command_names[command][0]
    except:
        return f"unknown type (0x{command:0X})"


def get_command(command, command_names):
    try:
        return command_names[command]
    except:
        return False


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
        if result:
            return offset
    return -1


def decode_header(header_4b):
    return Header(VALUE_TYPES(header_4b[0]), int.from_bytes(bytes(header_4b[:4]), "little"), 4)


def collection_check_full(collection):
    for value in collection.values():
        if value is None:
            return False
    return True


def set_value_in_collections(device, device_name, value_name, value):
    for col_key in device.collections.keys():
        if value_name in device.collections[col_key]:
            device.collections[col_key][value_name] = value
            device.collections[col_key][f'{value_name} Updated'] = f'{datetime.now():%Y-%m-%d %H:%M:%S}'
            logger.debug(f'{device_name}: Setting value in collection: {value_name} to {value}')
            return col_key
    return False


def handle_one_value(value, device_name, device):
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
        result, used = decode_fixed_len(value[consumed:])
        #if not command:
        #    logger.warning(f'{device_name}: {value}')
        #    return consumed


    if header.value_type == VALUE_TYPES.VAR_LEN:
        category = VARLEN_CATEGORY_LOOKUP[header.category_type]
        result, used = decode_var_len(value[consumed:], category[1])

    for i in range(len(result)):
        value_name = result[i]['command'][1]
        value = result[i]['value']

        if not device.collections or args.all:
            logger.debug(f'{device_name}: Collected {value_name} -> {value}')
            output(device_name, value_name, value)
        else:
            # Set collection value and check if collection is ready

            col_key = set_value_in_collections(device, device_name, value_name, value)
            if not col_key:
                logger.debug(f'{device_name}: {value_name} not in any collections, it will never be published')
            else:
                if collection_check_full(device.collections[col_key]):
                    logger.info(f'Collection is full, sending data via {device.config["logger"]}')
                    logger.debug(f'{device_name}: Collection:  {json.dumps(device.collections[col_key])}')
                    output(device_name, col_key, device.collections[col_key])

                    device.reset_collection(col_key)
                    if config['direct_disconnect']:
                        disconnect_loop(device.gatt_device)

    consumed += used

    return consumed


def decode_history_packet(command, value):
    total_length = value[DATA_POS]
    if len(value) < total_length:
        return "", -1

    values = []
    for config in SOLAR_HISTORY_VALUES:
        command = config[2]
        data = value[config[0] : config[0] + config[1]]
        values += [{"command": command, "value": convert_value_number(data, command)}]

    day_index = value[35]
    logger.debug(f"Day Index: {day_index -54} alternative (should match): {command-0x50}")
    return values, total_length


def decode_var_len(value, config_table):

    length_type_field = value[LENGHT_TYPE_POS]
    length = length_type_field & 0x0F
    type_id = (length_type_field & 0xF0) >> 4
    data = value[DATA_POS : DATA_POS + length]

    command = value[COMMAND_POS]
    #print(f'<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<{value}')
    #print(f'|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||{command}')
    if HISTORY_MIN_CMD <= command <= HISTORY_MAX_CMD:
        #print(f'!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! DECODING HISTORY PACKAGE!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        return decode_history_packet(command, value)

    if command not in config_table:
        raise KeyError(f"unknown command (in var len) 0x{command:x} in {config_table}")

    #data_label = get_label(command, config_table)
    #config = config_table[command]
    #data_string = format_value(data, config)
    command = get_command(command, config_table)
    value_string = command[5](data, command)

    consumed = 2 + length
    return [{"command": command, "value": value_string}], consumed


def decode_fixed_len(value):
    """function expects whole packet with 4-byte prefix"""
    DATATYPE_POS = 0
    DATA_POS = 1
    consumed = 2

    data = value[DATA_POS]
    data_type = value[DATATYPE_POS]
    command = get_command(data_type, MIXED_SETTINGS_NAMES)
    if not command:
        raise KeyError(f"unknown command (in fixed len) 0x{command:x}")
    value_string = convert_value(data, command)

    return [{"command": command, "value": value_string}], consumed



buffer = bytearray()


def handle_bulk_values(value, device_name, device):
    global buffer
    buffer.extend(value)

    pos = start_of_packet(buffer)
    while len(buffer) > 0 and pos >= 0:
        consumed = handle_one_value(buffer[pos:], device_name, device)
        if consumed == -1:
            logger.debug(f"UNRECOGNIZED DATA: {device_name}: bulk: need more bytes")
            return
        buffer = buffer[pos + consumed :]
        pos = start_of_packet(buffer)
        if pos > 0:  # TODO BUG: midnight hacking
            unknown = buffer[:pos]
            logger.debug(f"UNRECOGNIZED DATA: {device_name}: unknown value in bulk: {unknown}")


def handle_single_value(value, device_name, device):
    value_origin = copy.deepcopy(value)
    pos = start_of_packet(value)
    while pos >= 0:
        consumed = handle_one_value(value[pos:], device_name, device)
        value = value[pos + consumed :]
        pos = start_of_packet(value)
    if len(value) > 0:
        logger.debug(f"UNRECOGNIZED DATA: {device_name}: unknown single packet: value:{value} - value_origin:{value_origin}")


def connect_loop(device):
    try:
        device.connect()
    except:
        logger.error(f"{device.name}: failed to connect. Trying again shortly.")
        return False
    # maybe important. sleep(0) yields to other threads - give eventloop a chance to work
    time.sleep(0)
    #logger.info(f"{device.name}: connected: {device.connected}")
    if device.connected:
        device.subscribe_notifications()
        time.sleep(2)
        logger.debug(f"{device.name} send init sequence")
        device.start_send_init_squence()
        return True
    else:
        logger.error(f"{device.name}: failed to connect.")
        return False


def disconnect_loop(gatt_device):
    logger.info(f"{gatt_device.name}: disconnecting...")
    #gatt_device.unsubscribe_notifications()
    gatt_device.disconnect()
    return connect_loop


def connect_disconnect_loop(devices):
    #next_state = (0, connect_loop)
    i = 0
    while True:
        #try:
        if connect_loop(devices[i]):
            if args.keep_connected:
                pass
            elif config['direct_disconnect']:
                next_time = datetime.now() + timedelta(seconds=config['timer']['repeat'])
                logger.info(
                    f"{devices[i].name}: BT will reconnect in {config['timer']['repeat']} seconds. ({next_time:%H:%M:%S})")
                sleep(config['timer']['connected'])
            else:
                next_time = datetime.now() + timedelta(seconds=config['timer']['connected'])

                logger.info(f"{devices[i].name}: Bluetooth will disconnected in {config['timer']['connected']} seconds. ({next_time:%H:%M:%S})")
                sleep(config['timer']['connected'])

                disconnect_loop(devices[i])
                sleep(config['timer']['disconnected'])

        else:
            logger.info(f'{devices[i].name}: Reconnecting in {config["timer"]["retry"]}')
            sleep(config["timer"]["retry"])
        #except:
        #    # catch all to keep thread going
        #    traceback.print_stack()
        sleep(10)
        i = (i + 1) % len(devices)


def prepare_device(dev):
    logger.debug(f"{dev['name']} preparing...")

    if dev['type'] == 'smartshunt':
        device = victron_smartshunt.Smartshunt(config)
    elif dev['type'] == 'smartsolar':
        device = victron_smartsolar.Smartsolar(config)
    elif dev['type'] == 'orionsmart':
        device = victron_orion.get_device_instance(device['mac'], device['name'], handle_single_value, handle_bulk_values)

    gatt_device = device.get_gatt_device_instance(dev['mac'], dev['name'], handle_single_value, handle_bulk_values)

    return gatt_device


def get_serial_data(device):
    data = device.get_data()
    output(device.name, 'latest', data)


def get_helper_string_device(devices):
    return_string = ""
    for count, device in enumerate(devices):
        return_string += f"{count}: {device['name']} | "
    return return_string


def output_syslog(device, category, value):
    print(f"{device}|{category}:{value}", file=sys.stderr)
    subprocess.run(
        [
            "/usr/bin/logger",
            f"--id={os.getpid()}",
            "-t",
            "victron",
            f"{device}|{category}:{value}",
        ]
    )


def output_mqtt(device, category, value):
    global client

    if value == "":
        client.publish(f"victron/{device}", category)
    else:
        if type(value) is dict:
            data = json.dumps(value)
        else:
            data = '{"payload": ' + value + ' }'
        client.publish(f"victron/{device}/{category}", data)


if __name__ == "__main__":
    ## REMOVE LATER, ONLY FOR SEGFAULT DEBUGGING
    faulthandler.enable(all_threads=True)

    parser = argparse.ArgumentParser(description="Victron Reader (Bluetooth or Serial) \n\n"
                                                 "Current supported devices:\n"
                                                 "  Full: \n" 
                                                 "  Partial: \n"
                                                 "    - Smart Shunt (Bluetooth)\n"
                                                 "    - Smart Solar (Bluetooth)\n"
                                                 "    - Orion Smart (Bluetooth)\n"
                                                 "    - Phenoix Inverter (Serial)\n\n"
                                                 "Default behavior:\n"
                                                 "  1. It will connect to all known or given device\n"
                                                 "  2. Collect and log data summary as defined at the config file\n"
                                                 "  3. Disconnect and connect again at the time given by config file",
                                     formatter_class=argparse.RawTextHelpFormatter)
    group01 = parser.add_argument_group()
    group01.add_argument("--debug", action="store_true", help="Set log level to debug")
    group01.add_argument("--quiet", action="store_true", help="Set log level to error")

    group02 = parser.add_argument_group()
    group02.add_argument(
        "-p",
        "--print",
        action="store_true",
        help="Print only one time and exit",
        required=False,
    )
    group02.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Log / print all values as soon as they received [DEFAULT: Wait to collect all values given by Config]",
        required=False,
    )
    group02.add_argument(
        "-k",
        "--keep-connected",
        action="store_true",
        help="Keep connected to device [Default: Disconnect after receiving one collection of values, disconnection time set by config]",
        required=False,
    )
    group02.add_argument(
        "-t",
        "--direct-disconnect",
        action="store_true",
        help="Disconnect direct after getting one value [Default: Disconnect/Connect by time given in config]",
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

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        handler.setLevel(logging.DEBUG)
    elif args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
        handler.setLevel(logging.ERROR)

    config['keep_connected'] = args.keep_connected
    config['direct_disconnect'] = args.direct_disconnect

    if config['logger'] == 'mqtt':
        import paho.mqtt.client as mqtt

        client = mqtt.Client()
        client.connect(config['mqtt']['host'], config['mqtt']['port'], 60)
        client.loop_start()

        output = output_mqtt
    elif config['logger'] == 'syslog':
        output = output_syslog

    if args.device is not None:
        device = config['devices'][args.device]
        if device['protocol'] == 'bluetooth':
            devices = [prepare_device(device)]
            t1 = threading.Timer(0, connect_disconnect_loop, args=(devices,))
            #connect_disconnect_loop(devices)
        elif device['protocol'] == 'serial':
            if device['type'] == 'phoenix':
                get_serial_data(victron_phoenix.Phoenix(device['name'], device['port']))
    else:
        for count, device in enumerate(config['devices']):
            devices = []

            if device['protocol'] == 'bluetooth':
                devices.append(prepare_device(device))
            elif device['protocol'] == 'serial':
                if device['type'] == 'phoenix':
                    get_serial_data(victron_phoenix.Phoenix(device['name'], device['port']))

            t1 = threading.Timer(0, connect_disconnect_loop, args=(devices,))

    t1.start()

    logger.info("Gatt manager event loop starting...")
    victron_gatt.manager.run()
