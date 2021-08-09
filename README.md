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

Execute `python3 victron-new.py` after adding your SmartShunt to the configfile `config-new.yml`

The new script connect, gathering the data once and then disconnect. More features will be aded later. It is already way more stable without the connection problem like the other.
### Supported/tested devices:
Bluetooth:
- Smart Shunt
### Outputs
- mqtt
- syslog

## Ability of this repository
The script only tested with python 3.7 and 3.8.
### Supported/tested devices:
Bluetooth:
- Smart Shunt
- Smart Solar 100/30
- Orion Smart 12/12-30

Serial:
- Phoenix Inverter 12 800VA 230V

### Outputs
- mqtt
- syslog

### Autostart scripts
These scripts are written for my specific config file. If you have your devices in different order, you may need to adjust them.

## Howto use
If you want the serial communication with the Phoenix Inverter, you must install this library:
- vedirect: https://github.com/karioja/vedirect

You need to inbstall some requirements: `pip3 install -r requirements.txt`

Add your devices to the configuration file.
Start the script for your desired device: `python3 victrom.py -d 0`

There are some more commandline arguments, you can view them with `python3 victron.py --help`

## Known issues
- The bluetooth part have sometimes trouble to connect or just crashes. But systemd will restart the process automatically. I don't know why this happens and I don't know if it is a problem with this code or the gatt linux library. If you want to debug: Fell free!
- Orion Smart is not yet rewritten to the new classes and may not work correctly
- Drom smart solar you can't get the history values. The protocol itself is decoded (and working) for this part, but the smart solar doesn't send the data. I guess we need to send another init sequence. I didn't figure out the corrent sequence yet!
