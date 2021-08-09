def convert_value_number(value, command):
    converted = int.from_bytes(value, "little", signed=True)
    return str(converted / command[3])
