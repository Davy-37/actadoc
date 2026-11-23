"""DPE energy classes from the 2021 double-threshold scale."""

from decimal import Decimal

import pytest

from actadoc.generation._energy_classes import ENERGY_CLASSES, energy_class


@pytest.mark.parametrize(
    ("primary_energy", "expected"),
    [
        (0, "A"),
        (69, "A"),
        (70, "B"),  # bounds are excluded from the better class
        (109, "B"),
        (110, "C"),
        (180, "D"),
        (250, "E"),
        (330, "F"),
        (419, "F"),
        (420, "G"),
        (900, "G"),
    ],
)
def test_class_from_primary_energy(primary_energy, expected):
    assert energy_class(Decimal(primary_energy), Decimal(0)) == expected


@pytest.mark.parametrize(
    ("emissions", "expected"),
    [(5, "A"), (6, "B"), (11, "C"), (30, "D"), (50, "E"), (70, "F"), (99, "F"), (100, "G")],
)
def test_class_from_emissions(emissions, expected):
    assert energy_class(Decimal(0), Decimal(emissions)) == expected


@pytest.mark.parametrize(
    ("primary_energy", "emissions", "expected"),
    [(150, 8, "C"), (150, 60, "E"), (400, 8, "F"), (60, 120, "G")],
)
def test_worse_of_the_two_scales_wins(primary_energy, emissions, expected):
    assert energy_class(Decimal(primary_energy), Decimal(emissions)) == expected


def test_decimal_values_just_below_a_bound():
    assert energy_class(Decimal("69.9"), Decimal("5.9")) == "A"


def test_classes_are_ordered_from_best_to_worst():
    assert ENERGY_CLASSES == tuple("ABCDEFG")


@pytest.mark.parametrize(("primary_energy", "emissions"), [(-1, 0), (0, -1)])
def test_negative_values_are_rejected(primary_energy, emissions):
    with pytest.raises(ValueError, match="non-negative"):
        energy_class(Decimal(primary_energy), Decimal(emissions))
