import pytest

from lumberLibrary import lumber as L


def test_lumber_lookup_2x4():
    item = L.lumber("2x4")
    assert item.name == "2x4"
    assert item.nominal_thickness == 2
    assert item.nominal_width == 4
    assert item.actual_thickness == 1.5
    assert item.actual_width == 3.5
    assert 8 in item.common_lengths_ft


def test_lumber_lookup_unknown_raises():
    with pytest.raises(KeyError):
        L.lumber("3x9000")


@pytest.mark.parametrize(
    "name, expected_actual",
    [
        ("1x2",  (0.75, 1.5)),
        ("1x4",  (0.75, 3.5)),
        ("1x6",  (0.75, 5.5)),
        ("1x8",  (0.75, 7.25)),
        ("1x10", (0.75, 9.25)),
        ("1x12", (0.75, 11.25)),
        ("2x4",  (1.5,  3.5)),
        ("2x6",  (1.5,  5.5)),
        ("2x8",  (1.5,  7.25)),
        ("4x4",  (3.5,  3.5)),
        ("6x6",  (5.5,  5.5)),
    ],
)
def test_dimensional_lumber_undersize_rule(name, expected_actual):
    item = L.lumber(name)
    assert (item.actual_thickness, item.actual_width) == expected_actual


def test_actual_smaller_than_nominal_for_all_dimensional():
    for item in L.DIMENSIONAL_LUMBER.values():
        assert item.actual_thickness < item.nominal_thickness
        assert item.actual_width < item.nominal_width


def test_hardwood_4_4_lookup():
    s = L.hardwood("4/4")
    assert s.grade == "4/4"
    assert s.thickness_rough == 1.0
    assert s.thickness_surfaced == 0.75
    assert 6.0 in s.typical_widths


def test_hardwood_grades_are_quarter_inches():
    for grade, stock in L.HARDWOOD_STOCK.items():
        n, _, d = grade.partition("/")
        assert int(n) / int(d) == stock.thickness_rough


def test_hardwood_surfaced_smaller_than_rough():
    for stock in L.HARDWOOD_STOCK.values():
        assert stock.thickness_surfaced < stock.thickness_rough


def test_hardwood_unknown_raises():
    with pytest.raises(KeyError):
        L.hardwood("3/4")  # not a quarter-inch grade name


def test_board_feet_unit_definition():
    assert L.board_feet(1, 12, 12) == pytest.approx(1.0)
    assert L.board_feet(2, 12, 12) == pytest.approx(2.0)
    assert L.board_feet(1, 6, 144) == pytest.approx(6.0)


def test_board_feet_rejects_negative():
    with pytest.raises(ValueError):
        L.board_feet(-1, 12, 12)


def test_board_feet_zero():
    assert L.board_feet(0, 12, 12) == 0.0
    assert L.board_feet(1, 0, 12) == 0.0


def test_hardwood_board_feet_uses_rough_thickness():
    # 4/4 stock: rough=1.0, so a 6"x12" piece = 0.5 bf
    assert L.hardwood_board_feet("4/4", 6, 12) == pytest.approx(0.5)
    # 8/4 stock: rough=2.0, so same piece = 1.0 bf
    assert L.hardwood_board_feet("8/4", 6, 12) == pytest.approx(1.0)


def test_lumber_dataclass_is_frozen():
    item = L.lumber("2x4")
    with pytest.raises(Exception):
        item.actual_width = 99  # type: ignore[misc]
