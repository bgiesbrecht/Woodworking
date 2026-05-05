import math

import pytest

from lumberLibrary import units


@pytest.mark.parametrize(
    "text, expected",
    [
        ("3.5", 3.5),
        ("3 1/2", 3.5),
        ("3-1/2", 3.5),
        ("3   1/2", 3.5),
        ("1/2", 0.5),
        ("0", 0.0),
        ("0.0", 0.0),
        ("100", 100.0),
        ('3 1/2"', 3.5),
        ("3 1/2 in", 3.5),
        ("-1 1/2", -1.5),
        ("-1/2", -0.5),
    ],
)
def test_parse_length_inches(text, expected):
    assert units.parse_length(text) == pytest.approx(expected)


def test_parse_length_metric():
    assert units.parse_length("88.9mm") == pytest.approx(3.5)
    assert units.parse_length("89 mm") == pytest.approx(89 / 25.4)
    assert units.parse_length("10cm") == pytest.approx(100 / 25.4)
    assert units.parse_length("1m") == pytest.approx(1000 / 25.4)


def test_parse_length_feet():
    assert units.parse_length("1ft") == pytest.approx(12.0)
    assert units.parse_length("2'") == pytest.approx(24.0)


def test_parse_length_default_unit_metric():
    assert units.parse_length("89", default_unit="mm") == pytest.approx(89 / 25.4)


@pytest.mark.parametrize("bad", ["", "abc", "3 1/", "1/0", "3 mm cm", "3 1/2 ly"])
def test_parse_length_rejects(bad):
    with pytest.raises((ValueError, ZeroDivisionError)):
        units.parse_length(bad)


@pytest.mark.parametrize(
    "x, expected",
    [
        (0, "0"),
        (3.5, "3 1/2"),
        (0.5, "1/2"),
        (2.0, "2"),
        (0.0625, "1/16"),
        (3.75, "3 3/4"),
        (-3.5, "-3 1/2"),
        (1.999, "2"),  # rounds up
    ],
)
def test_to_fraction(x, expected):
    assert units.to_fraction(x) == expected


def test_to_fraction_custom_denominator():
    assert units.to_fraction(0.125, denominator=8) == "1/8"
    assert units.to_fraction(0.1, denominator=8) == "1/8"  # rounds


def test_to_fraction_rejects_bad_denominator():
    with pytest.raises(ValueError):
        units.to_fraction(1.0, denominator=0)


def test_round_trip_common_values():
    for src in ["1/2", "3 1/2", "5", "1/16", "11 5/8"]:
        decimal = units.parse_length(src)
        formatted = units.to_fraction(decimal)
        assert units.parse_length(formatted) == pytest.approx(decimal)


def test_inches_mm_round_trip():
    for x in [0.0, 0.5, 1.0, 89.0, 144.0]:
        assert units.mm_to_inches(units.inches_to_mm(x)) == pytest.approx(x)


def test_unit_constants():
    assert units.MM_PER_INCH == 25.4
    assert math.isclose(units.UNIT_TO_INCHES["mm"] * 25.4, 1.0)
