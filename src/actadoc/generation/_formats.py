"""French formatting of amounts, dates and surfaces, with their normalized forms."""

from __future__ import annotations

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

_MONTHS = (
    "janvier",
    "février",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
)


def format_amount(amount: Decimal) -> tuple[str, str]:
    """Format an amount in euros the French way.

    Parameters
    ----------
    amount : decimal.Decimal
        Amount in euros, ``>= 0``.

    Returns
    -------
    tuple of str
        Displayed form (``"1 250,00 €"``) and normalized form (``"1250.00"``).

    Raises
    ------
    ValueError
        If ``amount`` is negative.

    Examples
    --------
    >>> format_amount(Decimal("1250"))
    ('1 250,00 €', '1250.00')
    """
    if amount < 0:
        raise ValueError(f"amount must be non-negative, got {amount}")
    normalized = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    integer, cents = f"{normalized:.2f}".split(".")
    grouped = f"{int(integer):,}".replace(",", " ")
    return f"{grouped},{cents} €", str(normalized)


def format_date(day: date) -> tuple[str, str]:
    """Format a date the French way, as written in contracts.

    Parameters
    ----------
    day : datetime.date
        Date to format.

    Returns
    -------
    tuple of str
        Displayed form (``"1er mars 2026"``) and ISO 8601 form (``"2026-03-01"``).

    Examples
    --------
    >>> format_date(date(2026, 3, 1))
    ('1er mars 2026', '2026-03-01')
    """
    number = "1er" if day.day == 1 else str(day.day)
    return f"{number} {_MONTHS[day.month - 1]} {day.year}", day.isoformat()


def format_surface(square_metres: Decimal) -> tuple[str, str]:
    """Format a living area the French way, with one decimal.

    Parameters
    ----------
    square_metres : decimal.Decimal
        Area in square metres, ``> 0``.

    Returns
    -------
    tuple of str
        Displayed form (``"45,5 m²"``) and normalized form (``"45.5"``).

    Raises
    ------
    ValueError
        If ``square_metres`` is not positive.

    Examples
    --------
    >>> format_surface(Decimal("45.5"))
    ('45,5 m²', '45.5')
    """
    if square_metres <= 0:
        raise ValueError(f"surface must be positive, got {square_metres}")
    normalized = square_metres.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    return f"{normalized}".replace(".", ",") + " m²", str(normalized)
