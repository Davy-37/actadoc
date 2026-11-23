"""Energy classes of the French DPE, from the 2021 double-threshold scale."""

from __future__ import annotations

from decimal import Decimal

ENERGY_CLASSES = ("A", "B", "C", "D", "E", "F", "G")

# Upper bounds (excluded) of classes A to F; G has no upper bound.
# Primary energy in kWh/m²/year, emissions in kg CO2 eq/m²/year (arrêté du 31 mars 2021).
_ENERGY_BOUNDS = (70, 110, 180, 250, 330, 420)
_EMISSION_BOUNDS = (6, 11, 30, 50, 70, 100)


def _class_for(value: Decimal, bounds: tuple[int, ...]) -> str:
    """Return the class of ``value`` on a single scale."""
    for energy_class, bound in zip(ENERGY_CLASSES, bounds, strict=False):
        if value < bound:
            return energy_class
    return ENERGY_CLASSES[-1]


def energy_class(primary_energy: Decimal, emissions: Decimal) -> str:
    """Return the DPE class of a dwelling.

    The class is the worse of the class given by primary energy consumption
    and the class given by greenhouse gas emissions.

    Parameters
    ----------
    primary_energy : decimal.Decimal
        Primary energy consumption, in kWh/m²/year, ``>= 0``.
    emissions : decimal.Decimal
        Greenhouse gas emissions, in kg CO2 eq/m²/year, ``>= 0``.

    Returns
    -------
    str
        One of ``"A"`` to ``"G"``.

    Raises
    ------
    ValueError
        If ``primary_energy`` or ``emissions`` is negative.

    Examples
    --------
    >>> energy_class(Decimal("150"), Decimal("8"))
    'C'
    >>> energy_class(Decimal("150"), Decimal("60"))
    'E'
    """
    if primary_energy < 0 or emissions < 0:
        raise ValueError(
            f"consumption and emissions must be non-negative, got {primary_energy} and {emissions}"
        )
    return max(_class_for(primary_energy, _ENERGY_BOUNDS), _class_for(emissions, _EMISSION_BOUNDS))
