import pytest

from lumberLibrary import sheet_goods as sg


def test_lookup_ply_3_4():
    s = sg.sheet_good("ply_3/4")
    assert s.kind == "plywood"
    assert s.nominal_thickness == "3/4"
    assert s.thickness == pytest.approx(23 / 32)
    assert s.sheet_size == (48.0, 96.0)


def test_lookup_unknown_raises():
    with pytest.raises(KeyError):
        sg.sheet_good("ply_2x4")


def test_plywood_actual_below_nominal():
    for name in ("ply_1/4", "ply_3/8", "ply_1/2", "ply_5/8", "ply_3/4"):
        s = sg.sheet_good(name)
        nom = eval(s.nominal_thickness)  # "3/4" -> 0.75
        assert s.thickness < nom, f"{name} actual should be undersize"


def test_mdf_true_to_nominal():
    for name in ("mdf_1/4", "mdf_1/2", "mdf_3/4"):
        s = sg.sheet_good(name)
        assert s.thickness == eval(s.nominal_thickness)


def test_baltic_birch_is_5x5():
    for name in ("bb_1/4", "bb_1/2", "bb_3/4"):
        s = sg.sheet_good(name)
        assert s.sheet_size == (60.0, 60.0)


def test_area_helpers():
    s = sg.sheet_good("ply_3/4")
    assert s.area_sq_in == 48.0 * 96.0
    assert s.area_sq_ft == pytest.approx(32.0)


def test_by_kind():
    plywoods = sg.by_kind("plywood")
    assert len(plywoods) >= 5
    assert all(s.kind == "plywood" for s in plywoods)
    assert sg.by_kind("nonexistent") == []


def test_naive_sheets_needed():
    s = sg.sheet_good("ply_3/4")  # 32 sqft per sheet
    assert sg.naive_sheets_needed(0, s) == 0
    assert sg.naive_sheets_needed(1, s) == 1
    assert sg.naive_sheets_needed(32, s) == 1
    assert sg.naive_sheets_needed(32.001, s) == 2
    assert sg.naive_sheets_needed(96, s) == 3
    assert sg.naive_sheets_needed(96.5, s) == 4


def test_naive_sheets_needed_rejects_negative():
    s = sg.sheet_good("ply_3/4")
    with pytest.raises(ValueError):
        sg.naive_sheets_needed(-1, s)


def test_sheet_size_length_at_least_width():
    for s in sg.SHEET_GOODS.values():
        assert s.length >= s.width


def test_sheet_good_is_frozen():
    s = sg.sheet_good("ply_3/4")
    with pytest.raises(Exception):
        s.thickness = 0.5  # type: ignore[misc]
