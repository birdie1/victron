#!/usr/bin/env python3
import argparse
import copy
import faulthandler
import json
import logging
import os
import queue
import subprocess
import sys
import threading
import time
import yaml
from collections import namedtuple
from datetime import datetime, timedelta
from enum import IntEnum
from time import sleep

with open("config-new.yml", 'r') as ymlfile:
    config = yaml.full_load(ymlfile)


logger_format = '[%(levelname)-7s] (%(asctime)s) %(filename)s::%(lineno)d %(message)s'
logging.basicConfig(level=logging.DEBUG,
                    format=logger_format,
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename=f"logs/victron-new.log")
logger = logging.getLogger()

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter(logger_format)
handler.setFormatter(formatter)
logger.addHandler(handler)


def victron_thread(thread_count, config, vdevice_config, thread_q):
    from lib.victron import Victron
    v = Victron(config, vdevice_config, output, args, thread_count, thread_q)
    v.read()


def output_syslog(device, category, value):
    #print(f"{device}|{category}:{value}", file=sys.stderr)
    subprocess.run(
        [
            "/usr/bin/logger",
            f"--id={os.getpid()}",
            "-t",
            "victron",
            f"{device}|{category}:{value}",
        ]
    )


def output_mqtt(device_name, subtopic, value, hass_config=False):
    global client
    global config

    if hass_config:
        pub = subtopic
        data = value
    else:
        if value == "":
            pub = f'{config["mqtt"]["base_topic"]}/{device_name}'
            data = subtopic
        else:
            pub = f'{config["mqtt"]["base_topic"]}/{device_name}/{subtopic}'
            if type(value) is dict:
                data = json.dumps(value)
            else:
                data = value

    client.publish(pub, data)


def get_helper_string_device(devices):
    return_string = ""
    for count, device in enumerate(devices):
        return_string += f"{count}: {device['name']} | "
    return return_string


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Victron Reader (Bluetooth or Serial) \n\n"
                                                 "Current supported devices:\n"
                                                 "  Full: \n" 
                                                 "    - Phoenix Inverter (Serial)\n"
                                                 "    - Smart Shunt (Serial)\n"
                                                 "    - Smart Solar (Serial)\n"
                                                 "  Partial: \n"
                                                 "    - Smart Shunt (Bluetooth BLE)\n"
                                                 "Default behavior:\n"
                                                 "  1. It will connect to all known or given device\n"
                                                 "  2. Collect and log data summary as defined at the config file\n"
                                                 "  3. Disconnect",
                                     formatter_class=argparse.RawTextHelpFormatter)
    group01 = parser.add_argument_group()
    group01.add_argument("--debug", action="store_true", help="Set log level to debug")
    group01.add_argument("--quiet", action="store_true", help="Set log level to error")

    group02 = parser.add_argument_group()
    group02.add_argument(
        "-c",
        "--collection",
        action="store_true",
        help="Output only collections specified in config instead of single values",
        required=False,
    )

    group03 = parser.add_argument_group()
    group03.add_argument(
        "-d",
        "--device",
        metavar="NUM / NAME",
        type=str,
        help=get_helper_string_device(config['devices']),
        required=True,
    )
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        handler.setLevel(logging.DEBUG)
    elif args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
        handler.setLevel(logging.ERROR)

    #config['keep_connected'] = args.keep_connected
    #config['direct_disconnect'] = args.direct_disconnect

    if config['logger'] == 'mqtt':
        import paho.mqtt.client as mqtt

        client = mqtt.Client()
        client.connect(config['mqtt']['host'], config['mqtt']['port'], 60)

        client.loop_start()

        output = output_mqtt
    elif config['logger'] == 'syslog':
        output = output_syslog

    q = queue.Queue()

    # Build device list with all devices or just the given by commandline
    if args.device is not None:
        try:
            dev_id = int(args.device)
        except ValueError:
            for count, device_config in enumerate(config['devices']):
                if device_config['name'] == args.device:
                    dev_id = count
                    break
                logger.error(f'{args.device} not found in config')
                sys.exit(1)
        devices_config = [config['devices'][dev_id]]
    else:
        devices_config = config['devices']

    for count, device_config in enumerate(devices_config):
        t = threading.Timer(2+(count*5), victron_thread, args=(count, config, device_config, q))
        t.start()
