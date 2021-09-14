# VictronConnect Bluetooth & Serial

**This repository is in no way approved by or afiliated with the official Victron Energy repository.**
**I am not responsible for any problems or damages with your devices or this code**

**Only run this script if you are sure you know what you are doing!**

This repository is based on [https://github.com/vvvrrooomm/victron](https://github.com/vvvrrooomm/victron).

I use this repository to have a running version with mqtt for my camping car.
If you want more information about the development and a wireshard dissector, refer to vvvrrooomm's repository.

## New version for the new bluetooth gatt api used in the beta firmware of the SmartShunt
See [https://community.victronenergy.com/questions/93919/victron-bluetooth-ble-protocol-publication.html](https://community.victronenergy.com/questions/93919/victron-bluetooth-ble-protocol-publication.html)
for more information about how to activate the new gatt protocol with the beta firmware.

The new script connect, gathering the data once and then disconnect on Bluetooth BLE. Other Bluetooth stuff is still supported by the script.

More features will be added soon. 

### Supported/tested devices:
Bluetooth:
- Smart Shunt
### Outputs
- mqtt
- syslog

## Ability of this repository
The script only tested with python 3.7 and 3.8.
### Supported/tested devices:
Bluetooth BLE: 
- Smart Shunt

Bluetooth:
- Smart Shunt
- Smart Solar 100/30
- Orion Smart 12/12-30

Serial:
- Phoenix Inverter 12 800VA 230V
- Smart Shunt
- Smart Solar 100/30

### Outputs
- mqtt
- syslog

### Autostart scripts (systemd)
These scripts are written for my specific config file. If you have your devices in different order, you may need to adjust them.

## Howto use
If you want the serial communication with the Phoenix Inverter, you must install this library:
- vedirect: https://github.com/karioja/vedirect

You need to install some requirements: `pip3 install -r requirements.txt`

Add your devices to the configuration file.
Start the script for your desired device: `python3 victron.py -d 0`

There are some more commandline arguments, you can view them with `python3 victron.py --help`

## Known issues
- Orion Smart must be more reverse engineered to get some more interesting values
- Bluetooth: From smart solar you can't get the history values. The protocol itself is decoded (and working) for this part, but the smart solar doesn't send the data. I guess we need to send another init sequence. I didn't figure out the corrent sequence yet!
- Serial: Smart Solar history currently not gathered

## Future Plans:
- Choose via config file which values should be printed
- Choose how often values should be printed (especially bluettooth with notifications)
- CMD Parameter instead of config (easier testing of new devices)
- SmartSolar history values
