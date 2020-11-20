from victron_gatt import AnyDevice,smart_shunt_ids
from _pytest import fixtures
import pytest
from victron_2 import (
    handle_one_value,
    decode_var_len,
    start_of_packet,
    decode_header,
    VALUE_TYPES,
    CATEGORY_TYPES,
)
import types
import gatt

manager = gatt.DeviceManager(adapter_name="hci0")


def test_handle_knwon():
    FIXTURES = [
        ("080319ed8c4446fcffff", "Current: -0.954A", 10),
        ("080319ed8e42f3ff", "Power: -13W", 8),
        ("080319ed7d42ffff", "Starter: -0.01V", 8),
        ("080319ed8d422f05", "Voltage: 13.27V", 8),
    ]
    PREFIX_LENGTH = 4
    for data, expected, length in FIXTURES:
        input = bytes.fromhex(data)
        result, consumed = decode_var_len(input)

        assert result == expected
        assert consumed + PREFIX_LENGTH == length


def test_updated():
    fixtures = [
        ("0027", "080319ed8f42f8ff080319ed8c444efcffff0803"),
    ]
    device = AnyDevice("", manager)
    for handle, data in fixtures:
        dummy_characteristic = types.SimpleNamespace(uuid=smart_shunt_ids[handle])
        device.characteristic_value_updated(dummy_characteristic, bytes.fromhex(data))


def test_start_of_packet():  # 1 2 3 4 5 6 7 8 9 1011121314
    fixture = bytes.fromhex("080319030844c5320000080319ed8f42f7ff0803")
    pos = start_of_packet(fixture)
    assert pos == 0
    fixture = fixture[pos + 1 :]
    pos = start_of_packet(fixture)
    assert pos == 9
    fixture = fixture[pos + 1 :]
    pos = start_of_packet(fixture)
    assert pos == -1


def test_real_errors():
    fixtures = [
        (
            "0027",
            b"\xc5\x82\x99V\xa0\x00T\x01\x00\x00\xd1\xff\xff\xff\xff\x08\x03\x19\x03\x08",
        ),
    ]
    device = AnyDevice("", manager)
    for handle, data in fixtures:
        dummy_characteristic = types.SimpleNamespace(uuid=smart_shunt_ids[handle])
        device.characteristic_value_updated(dummy_characteristic, data)

def test_decode_header():
    fixtures = [
        (bytes.fromhex("0803190f"), VALUE_TYPES.VAR_LEN, CATEGORY_TYPES.SETTINGS2),
        (bytes.fromhex("09031903"), VALUE_TYPES.FIXED_LEN, CATEGORY_TYPES.HISTORY),
        (bytes.fromhex("090319ed"), VALUE_TYPES.FIXED_LEN, CATEGORY_TYPES.VALUES),
        (bytes.fromhex("0803190f"), VALUE_TYPES.VAR_LEN, CATEGORY_TYPES.SETTINGS2),

    ]
    for param in fixtures:
        result = decode_header(param[0])
        assert result.value_type == param[1]
        assert result.category_type == param[2]

def test_battery_capacity():
    fixtures = [
        ("0027",bytes.fromhex("0803190fff421027")),
    ]
    device = AnyDevice("", manager)
    for handle, data in fixtures:
        dummy_characteristic = types.SimpleNamespace(uuid=smart_shunt_ids[handle])
        device.characteristic_value_updated(dummy_characteristic, data)