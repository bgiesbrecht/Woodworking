"""Dimensional lumber and hardwood stock reference data.

All dimensions are in inches unless noted.

Pure Python — no FreeCAD imports.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Lumber:
    """A standard dimensional-lumber size (e.g. 2x4)."""

    name: str
    nominal_thickness: int
    nominal_width: int
    actual_thickness: float
    actual_width: float
    common_lengths_ft: tuple[int, ...]


@dataclass(frozen=True)
class HardwoodStock:
    """A hardwood thickness grade (e.g. 4/4, 8/4).

    ``thickness_rough`` is the nominal (rough-sawn) thickness used by mills and
    for board-foot pricing. ``thickness_surfaced`` is what a finished board
    typically measures after planing — what a woodworker should model with.
    """

    grade: str
    thickness_rough: float
    thickness_surfaced: float
    typical_widths: tuple[float, ...]


def _lumber(name: str, nom_t: int, nom_w: int, act_t: float, act_w: float,
            lengths_ft: tuple[int, ...]) -> tuple[str, Lumber]:
    return name, Lumber(name, nom_t, nom_w, act_t, act_w, lengths_ft)


_SOFTWOOD_LENGTHS = (6, 8, 10, 12, 14, 16)
_FRAMING_LENGTHS = (8, 10, 12, 14, 16)
_TIMBER_LENGTHS = (8, 10, 12, 16)


# Standard SPF / softwood dimensional lumber. Actual width follows the
# 1/2" undersize rule below 8" nominal and 3/4" undersize at 8" and above.
DIMENSIONAL_LUMBER: dict[str, Lumber] = dict(entry for entry in [
    _lumber("1x2",  1, 2,  0.75,  1.5,   _SOFTWOOD_LENGTHS),
    _lumber("1x3",  1, 3,  0.75,  2.5,   _SOFTWOOD_LENGTHS),
    _lumber("1x4",  1, 4,  0.75,  3.5,   _SOFTWOOD_LENGTHS),
    _lumber("1x6",  1, 6,  0.75,  5.5,   _SOFTWOOD_LENGTHS),
    _lumber("1x8",  1, 8,  0.75,  7.25,  _SOFTWOOD_LENGTHS),
    _lumber("1x10", 1, 10, 0.75,  9.25,  _SOFTWOOD_LENGTHS),
    _lumber("1x12", 1, 12, 0.75,  11.25, _SOFTWOOD_LENGTHS),
    _lumber("2x2",  2, 2,  1.5,   1.5,   _FRAMING_LENGTHS),
    _lumber("2x3",  2, 3,  1.5,   2.5,   _FRAMING_LENGTHS),
    _lumber("2x4",  2, 4,  1.5,   3.5,   _FRAMING_LENGTHS),
    _lumber("2x6",  2, 6,  1.5,   5.5,   _FRAMING_LENGTHS),
    _lumber("2x8",  2, 8,  1.5,   7.25,  _FRAMING_LENGTHS),
    _lumber("2x10", 2, 10, 1.5,   9.25,  _FRAMING_LENGTHS),
    _lumber("2x12", 2, 12, 1.5,   11.25, _FRAMING_LENGTHS),
    _lumber("4x4",  4, 4,  3.5,   3.5,   _TIMBER_LENGTHS),
    _lumber("4x6",  4, 6,  3.5,   5.5,   _TIMBER_LENGTHS),
    _lumber("6x6",  6, 6,  5.5,   5.5,   _TIMBER_LENGTHS),
])


# Hardwood is sold in quarter-inch thickness grades. Rough thickness is the
# pricing reference; surfaced thickness is what arrives after S4S milling.
_TYPICAL_HARDWOOD_WIDTHS = (4.0, 6.0, 8.0, 10.0, 12.0)

HARDWOOD_STOCK: dict[str, HardwoodStock] = {
    "4/4":  HardwoodStock("4/4",  1.00, 0.75,  _TYPICAL_HARDWOOD_WIDTHS),
    "5/4":  HardwoodStock("5/4",  1.25, 1.00,  _TYPICAL_HARDWOOD_WIDTHS),
    "6/4":  HardwoodStock("6/4",  1.50, 1.25,  _TYPICAL_HARDWOOD_WIDTHS),
    "8/4":  HardwoodStock("8/4",  2.00, 1.75,  _TYPICAL_HARDWOOD_WIDTHS),
    "12/4": HardwoodStock("12/4", 3.00, 2.75,  _TYPICAL_HARDWOOD_WIDTHS),
    "16/4": HardwoodStock("16/4", 4.00, 3.75,  _TYPICAL_HARDWOOD_WIDTHS),
}


def lumber(name: str) -> Lumber:
    """Look up a dimensional lumber spec by name (e.g. ``"2x4"``)."""
    try:
        return DIMENSIONAL_LUMBER[name]
    except KeyError as e:
        raise KeyError(f"unknown dimensional lumber: {name!r}") from e


def hardwood(grade: str) -> HardwoodStock:
    """Look up a hardwood stock grade (e.g. ``"4/4"``)."""
    try:
        return HARDWOOD_STOCK[grade]
    except KeyError as e:
        raise KeyError(f"unknown hardwood grade: {grade!r}") from e


def board_feet(thickness_in: float, width_in: float, length_in: float) -> float:
    """Compute board-feet from inch dimensions.

    1 board-foot = 144 cubic inches (1" thick x 12" wide x 12" long).
    For hardwood, pass ``thickness_rough`` — pricing convention is rough thickness.
    """
    if thickness_in < 0 or width_in < 0 or length_in < 0:
        raise ValueError("dimensions must be non-negative")
    return (thickness_in * width_in * length_in) / 144.0


def hardwood_board_feet(grade: str, width_in: float, length_in: float) -> float:
    """Board-feet for a piece of hardwood, computed on rough thickness."""
    stock = hardwood(grade)
    return board_feet(stock.thickness_rough, width_in, length_in)
