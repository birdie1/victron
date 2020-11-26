from _pytest import fixtures
import pytest
import types
import gatt
from pytest_mock import mocker
from victron_2 import (
    SIGNATURE,
    VARLEN_CATEGORY_LOOKUP,
    decode_var_len,
    handle_bulk_values,
    handle_single_value,
    start_of_packet,
    decode_header,
    VALUE_TYPES,
)
import victron_2
from victron_gatt import AnyDevice
import victron_smartshunt
import victron_orion


manager = gatt.DeviceManager(adapter_name="hci0")


def test_handle_known():
    FIXTURES = [
        ("080319ed8c4446fcffff", "Current: -0.954A", 10),
        ("080319ed8e42f3ff", "Power: -13.0W", 8),
        ("080319ed7d42ffff", "Starter: -0.01V", 8),
        ("080319ed8d422f05", "Voltage: 13.27V", 8),
    ]
    PREFIX_LENGTH = 4
    for data, expected, length in FIXTURES:
        input = bytes.fromhex(data)
        header = decode_header(input)
        category = VARLEN_CATEGORY_LOOKUP[header.category_type]
        result, consumed = decode_var_len(input[4:], category[1])

        assert result == expected
        assert consumed + PREFIX_LENGTH == length


def test_updated():
    fixtures = [
        ("0027", "080319ed8f42f8ff080319ed8c444efcffff0803"),
    ]
    device = victron_smartshunt.get_device_instance(
        "", "test", handle_single_value, handle_bulk_values
    )
    for handle, data in fixtures:
        dummy_characteristic = types.SimpleNamespace(
            uuid=victron_smartshunt.handle_uuid_map[handle]
        )
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
        ("0027", b"\xc5\x82\x99V\xa0\x00T\x01\x00\x00\xd1\xff\xff\xff\xff\x08\x03\x19\x03\x08"),
    ]
    device = victron_smartshunt.get_device_instance(
        "", "test", handle_single_value, handle_bulk_values
    )
    for handle, data in fixtures:
        dummy_characteristic = types.SimpleNamespace(
            uuid=victron_smartshunt.handle_uuid_map[handle]
        )
        device.characteristic_value_updated(dummy_characteristic, data)


HEADER_FIXTURES = [
    (bytes.fromhex("0803190f"), VALUE_TYPES.VAR_LEN, 0x0F190308),
    (bytes.fromhex("09031903"), VALUE_TYPES.FIXED_LEN, 0x03190309),
    (bytes.fromhex("090319ed"), VALUE_TYPES.FIXED_LEN, 0xED190309),
    (bytes.fromhex("0803190f"), VALUE_TYPES.VAR_LEN, 0x0F190308),
    (bytes.fromhex("080019ed"), VALUE_TYPES.VAR_LEN, 0xED190008),
    (bytes.fromhex("08001901"), VALUE_TYPES.VAR_LEN, 0x01190008),
]


def test_signatures():
    for fixture in HEADER_FIXTURES:
        result = start_of_packet(fixture[0])
        assert result == 0


def test_signatures_negative():
    # moight need update if bulk headers are added
    WRONG_SIGNATURES = [
        bytes.fromhex("080018ed"),
        bytes.fromhex("08041901"),
    ]
    for fixture in WRONG_SIGNATURES:
        result = start_of_packet(fixture)
        assert result == -1


def test_decode_header():

    for param in HEADER_FIXTURES:
        result = decode_header(param[0])
        assert result.value_type == param[1]
        assert result.category_type == param[2]


def test_battery_capacity(mocker):
    fixtures = [
        ("0024", bytes.fromhex("0803190fff421027")),
    ]

    logged_result = ""

    def mocked_logger(text):
        nonlocal logged_result
        logged_result = text

    device = victron_smartshunt.get_device_instance(
        "", "test", handle_single_value, handle_bulk_values
    )
    for handle, data in fixtures:
        dummy_characteristic = types.SimpleNamespace(
            uuid=victron_smartshunt.handle_uuid_map[handle]
        )
        mocker.patch("victron_2.logger", mocked_logger)
        device.characteristic_value_updated(dummy_characteristic, data)
        assert logged_result == "test: Battery Charge Status: 100.0%"


def test_orion(mocker):
    logged_result = ""

    def mocked_logger(text):
        nonlocal logged_result
        logged_result = text

    # not yet decoded, but header should be accepted
    fixtures = [  #
        ("001e", b"\x08\x00\x19\x01 D\x12\x07\x00\x00"),
        ("001e", b"\x08\x00\x19\xed\xbbB\xc5\x04"),
        ("001e", b"\x08\x00\x19\xed\xdbBT\x01"),
        ("001e", b"\x08\x00\x19\x01 D\x13\x07\x00\x00"),
        ("001e", b"\x08\x00\x19\xed\xdbB^\x01"),
        ("001e", b"\x08\x00\x19\x01 D\x14\x07\x00\x00"),
        ("001e", b"\x08\x00\x19\xed\xbbB\xc6\x04"),
    ]

    device = victron_orion.get_device_instance("", "test", handle_single_value, handle_bulk_values)
    for handle, data in fixtures:
        dummy_characteristic = types.SimpleNamespace(uuid=victron_orion.handle_uuid_map[handle])
        mocker.patch("victron_2.logger", mocked_logger)
        device.characteristic_value_updated(dummy_characteristic, data)


def test_bulk_stuff():
    fixtures = [
        ("0027", "080319ed8f42f8ff080319ed8c444efcffff0803"),
    ]
    device = victron_smartshunt.get_device_instance(
        "", "test", handle_single_value, handle_bulk_values
    )
    for handle, data in fixtures:
        dummy_characteristic = types.SimpleNamespace(
            uuid=victron_smartshunt.handle_uuid_map[handle]
        )
        device.characteristic_value_updated(dummy_characteristic, bytes.fromhex(data))
