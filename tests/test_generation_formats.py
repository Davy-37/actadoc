"""French formatting of amounts, dates and surfaces."""

from datetime import date
from decimal import Decimal

import pytest

from actadoc.generation._formats import format_amount, format_date, format_surface


@pytest.mark.parametrize(
    ("amount", "displayed", "normalized"),
    [
        (Decimal("0"), "0,00 €", "0.00"),
        (Decimal("850"), "850,00 €", "850.00"),
        (Decimal("1250"), "1 250,00 €", "1250.00"),
        (Decimal("1234567.891"), "1 234 567,89 €", "1234567.89"),
        (Decimal("0.005"), "0,01 €", "0.01"),  # half-up rounding
    ],
)
def test_format_amount(amount, displayed, normalized):
    assert format_amount(amount) == (displayed, normalized)


def test_negative_amount_is_rejected():
    with pytest.raises(ValueError):
        format_amount(Decimal("-1"))


@pytest.mark.parametrize(
    ("day", "displayed"),
    [
        (date(2026, 3, 1), "1er mars 2026"),
        (date(2026, 2, 2), "2 février 2026"),
        (date(2025, 12, 31), "31 décembre 2025"),
        (date(2024, 8, 15), "15 août 2024"),
    ],
)
def test_format_date(day, displayed):
    assert format_date(day) == (displayed, day.isoformat())


@pytest.mark.parametrize(
    ("surface", "displayed", "normalized"),
    [
        (Decimal("45.5"), "45,5 m²", "45.5"),
        (Decimal("18"), "18,0 m²", "18.0"),
        (Decimal("120.25"), "120,3 m²", "120.3"),
    ],
)
def test_format_surface(surface, displayed, normalized):
    assert format_surface(surface) == (displayed, normalized)


@pytest.mark.parametrize("surface", [Decimal("0"), Decimal("-3")])
def test_non_positive_surface_is_rejected(surface):
    with pytest.raises(ValueError):
        format_surface(surface)
