import json

## START: BLUETOOTH CONVERT FUNCTIONS
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
## END: BLUETOOTH CONVERT FUNCTIONS

# TODO: Merge Bluetooth and Serial convert functions

## START: SERIAL CONVERT FUNCTIONS
def convert_int_factor(value, command):
    try:
        int(value)
    except ValueError:
        return str(value)

    data = int(value) * command[3]
    if type(data) == int:
        return str(data)
    else:
        return f'{data:.2f}'


def convert_str_out(value, command):
    return value


def convert_map_out(value, command):
    return f'{value}: {command[3][value]}'


def convert_warn_ar(value, command):
    value = int(value)
    raw_str = f"{value}: "
    raw_helper = []
    for i in range(13, -1, -1):
        if (2 ** i) <= value:
            raw_helper.append(command[3][2 ** i])
            value = value - (2 ** i)
    if len(raw_helper) == 0:
        raw_helper.append('None')
    return raw_str + "|".join(raw_helper)


def convert_firmware(fw_raw, command):
    if fw_raw == b'\xff\xff\xff':
        return 'NO FIRMWARE'
    if fw_raw[0] == '0':
        return f'{fw_raw[1:2]}.{fw_raw[2:]}'
    else:
        return f'{fw_raw[0:1]}.{fw_raw[1:2]}{fw_raw[2:]}'


def convert_production_date(value, command):
    return f'year: 20{value[2:4]}, week: {value[4:6]}'
## END: SERIAL CONVERT FUNCTIONS


def collection_check_full(collection):
    for value in collection.values():
        if value is None:
            return False
    return True


def build_hass_discovery_config(device_name, model, serial, firmware, sensor_config, base_topic, subtopic, value_template, collection):
    """
    Builds the config for homeassistant mqtt discovery
    :param device_name: Name of device
    :param model: model description of device
    :param serial: serial number of device
    :param firmware: firmware of device
    :param sensor_config: mapping row from decive classes
    :param base_topic: MQTT base topic
    :param subtopic: Subtopic is either the name of the sensor (e.g. Voltage) or of the collection (e.g. latest)
    :param value_template: sensor (e.g. Voltage)
    :param collection: None or a collection
    :return:
    """
    hass_config_topic = f'homeassistant/sensor/{device_name}/{value_template.replace(" ", "_")}/config'
    hass_config_data = {}

    if collection is not None:
        hass_config_data["unique_id"] = f'{device_name}_{value_template}_{collection}_victron'
        hass_config_data["name"] = f'{device_name} {value_template}'
    elif sensor_config[2] == 'timestamp':
        hass_config_data["unique_id"] = f'{device_name}_{value_template}_victron'
        hass_config_data["name"] = f'{device_name} {value_template}'
    else:
        hass_config_data["unique_id"] = f'{device_name}_{subtopic}_victron'
        hass_config_data["name"] = f'{device_name} {subtopic}'

    if sensor_config[2] == '%':
        hass_config_data["device_class"] = 'battery'
    elif sensor_config[2] == 'V':
        hass_config_data["device_class"] = 'voltage'
    elif sensor_config[2] == 'A' or sensor_config[2] == 'Ah':
        hass_config_data["device_class"] = 'current'
    elif sensor_config[2] == 'W' or sensor_config[2] == 'Wh' or sensor_config[2] == 'kWh':
        hass_config_data["device_class"] = 'power'
    elif sensor_config[2] == 'Time':
        hass_config_data["device_class"] = 'timestamp'
    else:
        pass

    if sensor_config[2] != '' and sensor_config[2] != 'timestamp':
        hass_config_data["unit_of_measurement"] = sensor_config[2]

    if sensor_config[2] == 'timestamp':
        #hass_config_data["display_options"] = "date_time"
        hass_config_data["value_template"] = "{{ as_timestamp(now())  | timestamp_custom(\"%Y-%m-%d %H:%M:%S\") }}"

    if sensor_config[0] == 'Latest':
        hass_config_data["state_class"] = 'measurement'

    if sensor_config[0] == 'Time':
        hass_config_data["value_template"] = "{% if value|string == '-1.0' %}infinit{% else %}{{ value }} minutes{% endif %}"

    hass_config_data["state_topic"] = f'{base_topic}/{device_name}/{subtopic}'

    if collection is not None:
        hass_config_data["value_template"] = "{{ value_json['" + value_template + "'] }}"

    hass_device = {
        "identifiers": [f'victron_{device_name}'],
        "manufacturer": 'Victron',
        "model": f'{model} Serial: {serial}',
        "name": device_name,
        "sw_version": firmware
    }

    hass_config_data["device"] = hass_device

    return hass_config_topic, json.dumps(hass_config_data)


def send_hass_config_payload(device_name, pid, ser, fw, mapping_table, base_topic, output, collections):
    for key, value in mapping_table.items():
        subtopic = value[1]
        value_template = value[1]
        collection = None

        if collections is not None:
            for ckey, cvalue in collections.items():
                if value[1] in cvalue:
                    subtopic = ckey
                    collection = ckey

        hass_config_subtopic, hass_config_data = build_hass_discovery_config(
            device_name,
            pid,
            ser,
            fw,
            value,
            base_topic,
            subtopic,
            value_template,
            collection
        )

        output(device_name, hass_config_subtopic, hass_config_data, hass_config=True)

    if len(list(mapping_table.items())) > 0:
        subtopic_updated = list(mapping_table.items())[0][1][1]
    else:
        subtopic_updated = 'missing_mapping_table'

    # Add an updated timestamp sensor
    hass_config_subtopic, hass_config_data = build_hass_discovery_config(
        device_name,
        pid,
        ser,
        fw,
        ['', '', 'timestamp'],
        base_topic,
        subtopic_updated,
        'Updated',
        None
    )

    output(device_name, hass_config_subtopic, hass_config_data, True)
