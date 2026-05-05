"""Sheet-good reference data: plywood, MDF, hardboard, OSB, melamine.

All dimensions are in inches.

Pure Python — no FreeCAD imports.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class SheetGood:
    """A standard sheet stock SKU.

    ``thickness`` is the *actual* thickness; ``nominal_thickness`` is the label
    woodworkers buy by (e.g. "3/4" plywood is actually 23/32" thick).
    ``sheet_size`` is ``(width_in, length_in)`` with ``length >= width``.
    """

    name: str
    kind: str
    nominal_thickness: str
    thickness: float
    sheet_size: tuple[float, float]

    @property
    def width(self) -> float:
        return self.sheet_size[0]

    @property
    def length(self) -> float:
        return self.sheet_size[1]

    @property
    def area_sq_in(self) -> float:
        return self.width * self.length

    @property
    def area_sq_ft(self) -> float:
        return self.area_sq_in / 144.0


_FOUR_BY_EIGHT = (48.0, 96.0)
_FIVE_BY_FIVE = (60.0, 60.0)


# US imperial plywood: actual thickness is the labeled nominal less 1/32".
SHEET_GOODS: dict[str, SheetGood] = {
    "ply_1/4":  SheetGood("ply_1/4",  "plywood", "1/4",  7.0 / 32,  _FOUR_BY_EIGHT),
    "ply_3/8":  SheetGood("ply_3/8",  "plywood", "3/8",  11.0 / 32, _FOUR_BY_EIGHT),
    "ply_1/2":  SheetGood("ply_1/2",  "plywood", "1/2",  15.0 / 32, _FOUR_BY_EIGHT),
    "ply_5/8":  SheetGood("ply_5/8",  "plywood", "5/8",  19.0 / 32, _FOUR_BY_EIGHT),
    "ply_3/4":  SheetGood("ply_3/4",  "plywood", "3/4",  23.0 / 32, _FOUR_BY_EIGHT),

    # Baltic / Russian birch comes in 5x5 sheets, true to metric.
    "bb_1/4":   SheetGood("bb_1/4",   "baltic_birch", "1/4", 6.0 / 25.4,  _FIVE_BY_FIVE),
    "bb_1/2":   SheetGood("bb_1/2",   "baltic_birch", "1/2", 12.0 / 25.4, _FIVE_BY_FIVE),
    "bb_3/4":   SheetGood("bb_3/4",   "baltic_birch", "3/4", 18.0 / 25.4, _FIVE_BY_FIVE),

    # MDF and particle board are true to nominal.
    "mdf_1/4":  SheetGood("mdf_1/4",  "mdf", "1/4", 0.25, _FOUR_BY_EIGHT),
    "mdf_1/2":  SheetGood("mdf_1/2",  "mdf", "1/2", 0.5,  _FOUR_BY_EIGHT),
    "mdf_3/4":  SheetGood("mdf_3/4",  "mdf", "3/4", 0.75, _FOUR_BY_EIGHT),

    # Hardboard / Masonite.
    "hb_1/8":   SheetGood("hb_1/8",   "hardboard", "1/8", 0.125, _FOUR_BY_EIGHT),
    "hb_1/4":   SheetGood("hb_1/4",   "hardboard", "1/4", 0.25,  _FOUR_BY_EIGHT),
}


def sheet_good(name: str) -> SheetGood:
    """Look up a sheet good by name (e.g. ``"ply_3/4"``)."""
    try:
        return SHEET_GOODS[name]
    except KeyError as e:
        raise KeyError(f"unknown sheet good: {name!r}") from e


def by_kind(kind: str) -> list[SheetGood]:
    """All sheet goods of a given kind (``"plywood"``, ``"mdf"``, etc.)."""
    return [sg for sg in SHEET_GOODS.values() if sg.kind == kind]


def naive_sheets_needed(total_area_sq_ft: float, sheet: SheetGood) -> int:
    """A lower bound on sheets required by area alone (no layout, no waste).

    Real sheet-goods optimization (kerf, grain, off-cuts) is Phase 3 work via
    the bin-packer; this is a quick capacity check.
    """
    if total_area_sq_ft < 0:
        raise ValueError("total area must be non-negative")
    if total_area_sq_ft == 0:
        return 0
    return max(1, math.ceil(total_area_sq_ft / sheet.area_sq_ft))
