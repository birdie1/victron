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

version = 0.1


def victron_thread(thread_count, config, vdevice_config, thread_q):
    from lib.victron import Victron
    v = Victron(config, vdevice_config, output, args, thread_count, thread_q)
    v.connect_disconnect_loop()


def output_print(device_name, category, value, vunit=None):
    if type(value) == dict:
        map = {}
        map[category] = value
        print(json.dumps(map))
    else:
        print(f'{category}:{value}')


def output_json(device_name, category, value, vunit=None):
    map = {}
    if type(value) == dict:
        map[category] = value
    else:
        map[category] = {
            'value': value,
            'unit': vunit
        }
    print(json.dumps(map))


def output_syslog(device_name, category, value, vunit=None):
    if type(value) == dict:
        map = {}
        map[category] = value
        return_data = json.dumps(map)
    else:
        return_data = f"{device_name}|{category}:{value}"

    subprocess.run(
        [
            "/usr/bin/logger",
            f"--id={os.getpid()}",
            "-t",
            "victron",
            return_data,
        ]
    )


def mqtt_onconnect(client, userdata, flags, rc):
    client.publish(mqtt_lwt, payload=1, qos=0, retain=True)


def output_mqtt(device_name, subtopic, value, hass_config=False, vunit=None):
    global client
    global config
    retain = False

    if hass_config:
        pub = subtopic
        data = value
        retain = True
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

    client.publish(pub, data, retain=retain)


def get_helper_string_device(devices):
    return_string = ""
    for count, device in enumerate(devices):
        return_string += f"{count}: {device['name']} | "
    return return_string


def check_if_required_device_argument():
    for x in ['-h', '--help', '-v', '--version']:
        if x in sys.argv:
            return False
    return True

if __name__ == "__main__":
    if os.path.exists('config.yml'):
        with open('config.yml', 'r') as ymlfile:
            config = yaml.full_load(ymlfile)
    else:
        config = None

    parser = argparse.ArgumentParser(description="Victron Reader (Bluetooth, BLE and Serial) \n\n"
                                                 "Current supported devices:\n"
                                                 "  Full: \n" 
                                                 "    - Smart Shunt (Bluetooth BLE)\n"
                                                 "    - Phoenix Inverter (Serial)\n"
                                                 "    - Smart Shunt (Serial)\n"
                                                 "    - Smart Solar (Serial)\n"
                                                 "    - Blue Solar (Serial)\n"
                                                 "  Partial: \n"
                                                 "    - Smart Shunt (Bluetooth)\n"
                                                 "    - Smart Solar (Bluetooth)\n"
                                                 "    - Orion Smart (Bluetooth)\n"
                                                 "Default behavior:\n"
                                                 "  1. It will connect to given device\n"
                                                 "  2. Collect and log data summary as defined at the config file\n"
                                                 "  3. Disconnect and start over with timers set in config file",
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
    group02.add_argument(
        "-C",
        "--config-file",
        type=str,
        help="Specify different config file [Default: config.yml]",
        required=False,
    )
    group02.add_argument(
        "-D",
        "--direct-disconnect",
        action="store_true",
        help="Disconnect direct after getting values",
        required=False,
    )
    group02.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="Show version and exit",
        required=False,
    )

    group03 = parser.add_argument_group()
    group03.add_argument(
        "-d",
        "--device",
        metavar="NUM / NAME",
        type=str,
        help=get_helper_string_device(config['devices']) if config is not None else "",
        required=check_if_required_device_argument(),
    )
    args = parser.parse_args()

    if args.version:
        print(version)
        sys.exit(0)

    if args.config_file:
        with open(args.config_file, 'r') as ymlfile:
            config = yaml.full_load(ymlfile)

    if config is None:
        print("config.yml missing. Please create or specify another config file with -C")
        sys.exit(1)

    try:
        dev_id = int(args.device)
    except ValueError:
        for count, device_config in enumerate(config['devices']):
            if device_config['name'] == args.device:
                dev_id = count
                break
            print(f'{args.device} not found in config')
            sys.exit(1)
    devices_config = config['devices'][dev_id]

    logger_format = '[%(levelname)-7s] (%(asctime)s) %(filename)s::%(lineno)d %(message)s'
    logging.basicConfig(level=logging.INFO,
                        format=logger_format,
                        datefmt='%Y-%m-%d %H:%M:%S',
                        filename=f'logs/victron-{devices_config["name"]}.log')
    logger = logging.getLogger()

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(logger_format)
    handler.setFormatter(formatter)

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        handler.setLevel(logging.DEBUG)
    elif args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
        handler.setLevel(logging.ERROR)

    if config['logger'] == 'mqtt':
        logger.addHandler(handler)

        import paho.mqtt.client as mqtt
        client = mqtt.Client()
        if "username" in config['mqtt'] and "password" in config['mqtt']:
            client.username_pw_set(username=config['mqtt']['username'],password=config['mqtt']['password'])

        mqtt_lwt = f'{config["mqtt"]["base_topic"]}/{devices_config["name"]}/online'
        client.will_set(mqtt_lwt, payload=0, qos=0, retain=True)
        client.on_connect = mqtt_onconnect

        client.connect(config['mqtt']['host'], config['mqtt']['port'], 60)
        client.loop_start()

        output = output_mqtt
    elif config['logger'] == 'syslog':
        logger.addHandler(handler)
        output = output_syslog
    elif config['logger'] == 'print':
        output = output_print
    elif config['logger'] == 'json':
        output = output_json
    else:
        logger.addHandler(handler)
        logger.error('No output specified!')
        sys.exit(1)

    q = queue.Queue()

    t = threading.Timer(2+(1*5), victron_thread, args=(1, config, devices_config, q))
    t.start()
