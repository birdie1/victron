# VictronConnect Bluetooth & Serial

**This repository is in no way approved by or affiliated with the official Victron Energy repository.**
**I am not responsible for any problems or damages with your devices or this code**

**Only run this script if you are sure you know what you are doing!**

This repository is based on [https://github.com/vvvrrooomm/victron](https://github.com/vvvrrooomm/victron).

I use this repository to have a running version with mqtt for my camping car.
If you want more information about the development and a wireshark dissector, refer to vvvrrooomm's repository.

## New version for the new bluetooth gatt api used in the beta firmware of the SmartShunt
See [https://community.victronenergy.com/questions/93919/victron-bluetooth-ble-protocol-publication.html](https://community.victronenergy.com/questions/93919/victron-bluetooth-ble-protocol-publication.html)
for more information about how to activate the new gatt protocol with the beta firmware.

The new script connect, gathering the data once and then disconnect on Bluetooth BLE. Other Bluetooth stuff is still supported by the script.

More features will be added soon. 

## Ability of this repository
The script is tested with python > 3.7
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
- print

### Autostart scripts (systemd)
These scripts are written for my specific config file. If you have your devices in different order, you may need to adjust them.

## Howto use
If you want the serial communication with the Phoenix Inverter, you must install this library:
- vedirect: https://github.com/karioja/vedirect

You need to install some requirements: `pip3 install -r requirements.txt`

Add your devices to the configuration file.
Start the script for your desired device: `python3 victron.py -d 0`

There are some more commandline arguments, you can view them with `python3 victron.py --help`

### Configuration in detail
#### Device section
**Mandatory:**
Name, Type, Protocol and (MAC or serialport) depending of the type. bluetooth and bluetooth-ble need to have the bluetooth mac adress of the victron device specified.
<br>
Name: Choose yourself<br>
Type: phoenix, smartshunt, smartsolar, orionsmart<br>
Protocol: serial, bluetooth, bluetooth-ble
```buildoutcfg
    - name: Phoenix1
      type: phoenix
      protocol: serial
      port: /dev/victron-phoenix
```
or
```buildoutcfg
    - name: Shunt1
      type: smartshunt
      protocol: bluetooth-ble
      mac: fd:d4:50:0f:6c:1b
```
or
```buildoutcfg
    - name: Solar1
      type: smartsolar
      protocol: bluetooth
      mac: F9:8E:1C:EC:9C:72
```
**Optional:**


#### Output section
You can choose between:
```buildoutcfg
logger: mqtt
```
or 
```buildoutcfg
logger: syslog
```
#### MQTT section
Choose host, port, base_topic and if you want to use HomeAssistant Discovery (Yet only supported on serial devices). SSL and authentication will be added later.
```buildoutcfg
mqtt:
    host: 192.168.3.2
    port: 1883
    base_topic: victron
    hass: True
```
#### Collections section
You can specify if you want the values get summarized into one json output statement. Otherwise it will send out every value as soon as it is collected from victron device. 
```buildoutcfg
collections:
  smartshunt:
    device:
      - Product ID
      - Firmware Version
    battery:
      - State Of Charge
      - Time To Go
    latest:
      - Voltage
      - Current
      - Power
      - Starter Battery Voltage
      - Used Energy
    history:
      - Deepest Discharge
      - Last Discharge
      - Average Discharge
      - Cumulative Ah Drawn
      - Time Since Last Full
      - Charge Cycles
      - Full Discharges
      - Battery Voltage min
      - Battery Voltage max
      - Synchonisations
      - Alarm Voltage low
      - Alarm Voltage high
      - Starter Battery Voltage min
      - Starter Battery Voltage max
      - Total Discharged Energy
      - Total Charged Energy
  ...
```
## Known issues
- Orion Smart must be more reverse engineered to get some more interesting values
- Bluetooth: From smart solar you can't get the history values. The protocol itself is decoded (and working) for this part, but the smart solar doesn't send the data. I guess we need to send another init sequence. I didn't figure out the corrent sequence yet!
- Serial: Smart Solar history currently not gathered

## Future plans:
- Choose via config file which values should be printed
- Choose how often values should be printed (especially bluettooth with notifications)
- CMD Parameter instead of config (easier testing of new devices)
- SmartSolar history values
