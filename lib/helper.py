def convert_value_number(value, command):
    converted = int.from_bytes(value, "little", signed=True)
    return str(converted / command[3])


def convert_int_factor(value, command):
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
    if fw_raw[0] == '0':
        return f'{fw_raw[1:2]}.{fw_raw[2:]}'
    else:
        return f'{fw_raw[0:1]}{fw_raw[1:2]}.{fw_raw[2:]}'


def convert_production_date(value, command):
    return f'year: 20{value[2:4]}, week: {value[4:6]}'


def collection_check_full(collection):
    for value in collection.values():
        if value is None:
            return False
    return True
