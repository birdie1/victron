from _pytest import fixtures
import pytest
from victron_2 import handle_known_values, decode_value


def test_handle_knwon():
    FIXTURES = [
        ("080319ed8c4446fcffff", "Current: -0.954A"),
        ("080319ed8e42f3ff", "Power: -13W"),
        ("080319ed7d42ffff", "Starter: -0.01V"),
        ("080319ed8d422f05", "Voltage: 13.27V"),
    ]
    for data, expected in FIXTURES:
        input = bytes.fromhex(data)
        result = decode_value(input)

        assert result == expected


def test_negative():
    fixtures = [
        b"\xed\x8eB\xaa\xff\x08\x03\x19\x0f\xfeB\xb1\x06\x08\x00\x19\xec0A\x02",
        b"\xff\x08\x03\x19\xed\x8cD\xf9\xe6\xff\xff",
    ]
    for i in fixtures:
        print(f"fixture: {i}")
        handle_known_values(i)
