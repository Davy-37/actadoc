"""French formatting of amounts, dates, surfaces and cadastral references."""

from datetime import date
from decimal import Decimal

import pytest

from actadoc.generation._formats import (
    format_amount,
    format_cadastral_reference,
    format_date,
    format_surface,
)


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


@pytest.mark.parametrize(
    ("section", "number", "displayed", "normalized"),
    [
        ("AB", 123, "section AB n° 123", "AB0123"),
        ("C", 7, "section C n° 7", "0C0007"),
        ("ZZ", 9999, "section ZZ n° 9999", "ZZ9999"),
        ("A", 1, "section A n° 1", "0A0001"),
    ],
)
def test_format_cadastral_reference(section, number, displayed, normalized):
    assert format_cadastral_reference(section, number) == (displayed, normalized)


@pytest.mark.parametrize("section", ["", "ABC", "ab", "A1", "É"])
def test_invalid_cadastral_section_is_rejected(section):
    with pytest.raises(ValueError, match="section"):
        format_cadastral_reference(section, 1)


@pytest.mark.parametrize("number", [0, -1, 10000])
def test_invalid_parcel_number_is_rejected(number):
    with pytest.raises(ValueError, match="parcel number"):
        format_cadastral_reference("AB", number)
