"""Length parsing and fractional-inch formatting.

Pure Python — no FreeCAD imports.
"""

from __future__ import annotations

import re
from fractions import Fraction

MM_PER_INCH = 25.4

UNIT_TO_INCHES = {
    "in": 1.0,
    '"': 1.0,
    "ft": 12.0,
    "'": 12.0,
    "mm": 1.0 / MM_PER_INCH,
    "cm": 10.0 / MM_PER_INCH,
    "m": 1000.0 / MM_PER_INCH,
}

_LENGTH_RE = re.compile(
    r"""
    ^\s*
    (?P<sign>-)?
    (?:
        (?P<whole>\d+(?:\.\d+)?)
        (?:[\s-]+(?P<num>\d+)\s*/\s*(?P<den>\d+))?
        |
        (?P<num_only>\d+)\s*/\s*(?P<den_only>\d+)
    )
    \s*
    (?P<unit>in|ft|mm|cm|m|"|')?
    \s*$
    """,
    re.VERBOSE,
)


def parse_length(s: str, default_unit: str = "in") -> float:
    """Parse a length string and return inches.

    Accepts decimals, simple fractions, mixed numbers, and metric units.
    Examples that all return 3.5: ``"3 1/2"``, ``"3-1/2"``, ``"3.5"``,
    ``'3 1/2"'``, ``"88.9mm"``.
    """
    m = _LENGTH_RE.match(s)
    if not m:
        raise ValueError(f"could not parse length: {s!r}")

    if m["whole"] is not None:
        value = float(m["whole"])
        if m["num"] is not None:
            value += int(m["num"]) / int(m["den"])
    else:
        value = int(m["num_only"]) / int(m["den_only"])

    if m["sign"]:
        value = -value

    unit = m["unit"] or default_unit
    if unit not in UNIT_TO_INCHES:
        raise ValueError(f"unknown unit: {unit!r}")
    return value * UNIT_TO_INCHES[unit]


def inches_to_mm(x: float) -> float:
    return x * MM_PER_INCH


def mm_to_inches(x: float) -> float:
    return x / MM_PER_INCH


def to_fraction(x: float, denominator: int = 16) -> str:
    """Format an inch value as a reduced fractional string.

    ``3.5`` -> ``"3 1/2"``; ``0.5`` -> ``"1/2"``; ``2.0`` -> ``"2"``.
    Rounds to the nearest ``1/denominator`` (default 1/16).
    """
    if denominator <= 0:
        raise ValueError("denominator must be positive")
    if x == 0:
        return "0"

    sign = "-" if x < 0 else ""
    x = abs(x)
    whole = int(x)
    remainder = x - whole

    numerator = round(remainder * denominator)
    if numerator == denominator:
        whole += 1
        numerator = 0

    if numerator == 0:
        return f"{sign}{whole}"

    f = Fraction(numerator, denominator)
    if whole == 0:
        return f"{sign}{f.numerator}/{f.denominator}"
    return f"{sign}{whole} {f.numerator}/{f.denominator}"
