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
