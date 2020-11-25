#!/usr/bin/env python3

"""
Simple script to connect to a Phoenix Inverter and fetch some data
Requires a BT-dongle

This device requires to be paired to work.  Default pin = "000000"
This is only needed the first time you connect to a device

The easiest way to do that is to run 

$ bluetootctl
[bluetooth]# scan on
(...)
[bluetooth]# scan off
[bluetooth]# devices
(...)
Device DE:33:11:25:xx:xx VE.Direct Smart
(...)
[bluetooth]# connect DE:33:11:25:xx:xx
Attempting to connect to DE:33:11:25:xx:xx
Connection successful

[VE.Direct Smart]# trust 
Changing DE:33:11:25:xx:xx trust succeeded

[VE.Direct Smart]# pair
Attempting to pair with DE:33:11:25:xx:xx
Request passkey
[agent] Enter passkey (number in 0-999999): 000000
Pairing successful
[VE.Direct Smart]# 

You can then exit from bluetoothctl

Or you can use "menu gatt" and start looking at the different characteristics, and enable notifications for them to see what happens




"""

import gatt
import time
import threading
from datetime import datetime, timedelta

#  Set to your BT-device MAC-address
mac_address = "fd:d4:50:0f:6c:1b"

device_manager = gatt.DeviceManager(adapter_name="hci0")
device_manager.update_devices()

# device_manager.start_discovery()
# time.sleep(5)
# device_manager.stop_discovery()


characteristics = {}


class PhoenixDevice(gatt.Device):
    def __init__(self, mac_address, manager):
        super().__init__(mac_address=mac_address, manager=manager)
        self.last_notify = datetime.now() + timedelta(seconds=10)
        self.char_buffer = {}
        print("init")

    def characteristic_enable_notifications_succeeded(
        self,
        characteristic,
    ):
        print("[{}] Notifications enabled...".format(characteristic.uuid))

    def characteristic_enable_notifications_failed(self, characteristic, error):
        print("[{}] Notifications not enabled {}".format(characteristic.uuid, error))

    def characteristic_value_updated(self, characteristic, value):
        print("characteristic updated")
        self.last_notify = datetime.now()
        if (
            (characteristic.uuid == "306b0001-b081-4037-83dc-e59fcc3cdfd0")
            or (characteristic.uuid == "306b0002-b081-4037-83dc-e59fcc3cdfd0")
            or (characteristic.uuid == "306b0003-b081-4037-83dc-e59fcc3cdfd0")
            or (characteristic.uuid == "306b0004-b081-4037-83dc-e59fcc3cdfd0")
        ):
            print("[{}] Changed to {}".format(characteristic.uuid, value))
            self.getBulkValue(characteristic.uuid, value)
        elif characteristic.uuid == "306b0003-b081-4037-83dc-e59fcc3cdfd0":
            pass
        else:
            print("[{}] Changed to {}".format(characteristic.uuid, value))
            self.getValue(characteristic.uuid, value)


print("create device")
device = PhoenixDevice(mac_address=mac_address, manager=device_manager)

print("connect")
device.connect()
print("connect done")
# print("sl<eep 5")
# time.sleep(5)

logger_name = "x"

print("enumarete")
for service in device.services:
    print("[{}]  Service [{}]".format(logger_name, service.uuid))
    for characteristic in service.characteristics:
        print("[{}]    Characteristic [{}]".format(logger_name, characteristic.uuid))
        characteristics[characteristic.uuid] = characteristic


char_ids = {
    "0020": "306b0002-b081-4037-83dc-e59fcc3cdfd0",
    "0023": "306b0003-b081-4037-83dc-e59fcc3cdfd0",
    "0026": "306b0004-b081-4037-83dc-e59fcc3cdfd0",
}

# print("manager run")
# t1 = threading.Thread(target=lambda: device_manager.run())
# t1.daemon = True
# t1.start()

print("write init sequence")
c = characteristics["306b0002-b081-4037-83dc-e59fcc3cdfd0"]
hs = "fa80ff"
b = bytearray.fromhex(hs)
c.write_value(b)

hs = "f980"
b = bytearray.fromhex(hs)
c.write_value(b)

hs = "01"
b = bytearray.fromhex(hs)
c.write_value(b)

c = characteristics["306b0003-b081-4037-83dc-e59fcc3cdfd0"]

hs = "01"
b = bytearray.fromhex(hs)
c.write_value(b)

hs = "0300"
b = bytearray.fromhex(hs)
c.write_value(b)

hs = "060082189342102703010303"
b = bytearray.fromhex(hs)
c.write_value(b)

c = characteristics["306b0002-b081-4037-83dc-e59fcc3cdfd0"]
hs = "f941"
b = bytearray.fromhex(hs)
c.write_value(b)

print("device loop")
device_manager.run()
print("finished")
while True:
    pass


def device_poller():
    i = 0
    while 1:
        # Just a simple loop to send different commands towards the device
        time.sleep(1)
        if device.last_notify < datetime.now() - timedelta(seconds=10):
            # Seems like I need to send this from time to time to keep the
            # notification flowing.  If I don't they stop after everything form
            # a few seconds to a couple of minutes
            print("Sending push for refreshed data")
            c = characteristics["306b0002-b081-4037-83dc-e59fcc3cdfd0"]
            hs = "f941"
            b = bytearray.fromhex(hs)
            c.write_value(b)

        # Just testing how to turn the power on/off/eco and watching what happens
        if i == 20:
            c = characteristics["306b0003-b081-4037-83dc-e59fcc3cdfd0"]
            device.setPowerSwitch(c, "eco")
            time.sleep(1)
            c = characteristics["306b0002-b081-4037-83dc-e59fcc3cdfd0"]
            hs = "f941"
            b = bytearray.fromhex(hs)
            c.write_value(b)
        if i == 50:
            c = characteristics["306b0003-b081-4037-83dc-e59fcc3cdfd0"]
            device.setPowerSwitch(c, "on")
            time.sleep(1)
            c = characteristics["306b0002-b081-4037-83dc-e59fcc3cdfd0"]
            hs = "f941"
            b = bytearray.fromhex(hs)
            c.write_value(b)
        if i == 70:
            c = characteristics["306b0003-b081-4037-83dc-e59fcc3cdfd0"]
            device.setPowerSwitch(c, "off")
            time.sleep(1)
            c = characteristics["306b0002-b081-4037-83dc-e59fcc3cdfd0"]
            hs = "f941"
            b = bytearray.fromhex(hs)
            c.write_value(b)
        if i == 100:
            i = 0
        i = i + 1
