"""Generator of synthetic energy performance certificates (DPE) for dwellings."""

from __future__ import annotations

import random
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from faker import Faker

from actadoc.generation._base import DocumentGenerator, register_generator
from actadoc.generation._builder import DocumentBuilder
from actadoc.generation._energy_classes import energy_class
from actadoc.generation._formats import format_amount, format_date, format_surface
from actadoc.generation._schema import DocumentType, EntityType

# Range of issue dates, fixed so that the corpus does not depend on the run date.
_FIRST_ISSUE = date(2024, 1, 1)
_ISSUE_SPAN_DAYS = 900
_VALIDITY_YEARS = 10
# Rough cost of one kWh of primary energy, used only to make costs plausible.
_COST_PER_KWH = Decimal("0.12")


def _add_years(day: date, years: int) -> date:
    """Return the same day ``years`` later; 29 February becomes 28 February."""
    try:
        return day.replace(year=day.year + years)
    except ValueError:
        return day.replace(year=day.year + years, day=28)


def _round_to_ten(amount: Decimal) -> Decimal:
    """Round an amount to the nearest ten euros."""
    return (amount / 10).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * 10


@register_generator(DocumentType.ENERGY_CERTIFICATE)
class EnergyCertificateGenerator(DocumentGenerator):
    """Generate energy performance certificates for a dwelling.

    Entities produced, in reading order: owner and diagnostician (``party``),
    living area (``surface``), minimum and maximum estimated annual energy
    costs (``amount``), issue date and expiry date (``date``).

    The energy class, primary energy consumption and emissions are written in
    the text but not labelled: they are not one of the six entity types. The
    class always matches the two values (see :func:`energy_class`). The
    certificate is valid for ten years.

    Parameters
    ----------
    locale : str, default="fr_FR"
        Faker locale used for names, companies and addresses.
    """

    def _compose(self, builder: DocumentBuilder, fake: Faker, rng: random.Random) -> None:
        """Write an energy performance certificate into ``builder``."""
        owner = fake.name()
        diagnostician = fake.name()
        while diagnostician == owner:
            diagnostician = fake.name()
        company = fake.company()
        address = fake.address().replace("\n", ", ")
        certificate_number = f"{rng.randrange(10**12):012d}"

        area = Decimal(rng.randrange(150, 1500)) / 10
        surface, surface_norm = format_surface(area)
        primary_energy = Decimal(rng.randrange(50, 551))
        emissions = (primary_energy * Decimal(rng.randrange(2, 26)) / 100).quantize(Decimal("1"))
        rating = energy_class(primary_energy, emissions)

        yearly_cost = primary_energy * area * _COST_PER_KWH
        cost_min, cost_min_norm = format_amount(_round_to_ten(yearly_cost * Decimal("0.8")))
        cost_max, cost_max_norm = format_amount(_round_to_ten(yearly_cost * Decimal("1.2")))

        issued_on = _FIRST_ISSUE + timedelta(days=rng.randrange(_ISSUE_SPAN_DAYS))
        issue, issue_norm = format_date(issued_on)
        expiry, expiry_norm = format_date(_add_years(issued_on, _VALIDITY_YEARS))

        (
            builder.text(
                "DIAGNOSTIC DE PERFORMANCE ÉNERGÉTIQUE (logement)\n"
                f"N° de diagnostic : {certificate_number}\n\n"
                f"Adresse du bien : {address}\n"
                "Propriétaire : "
            )
            .entity(owner, EntityType.PARTY, "owner")
            .text("\nDiagnostiqueur : ")
            .entity(diagnostician, EntityType.PARTY, "diagnostician")
            .text(f", {company}\nSurface habitable : ")
            .entity(surface, EntityType.SURFACE, "living_area", surface_norm)
            .text(
                "\n\nPERFORMANCE ÉNERGÉTIQUE ET CLIMATIQUE\n"
                f"Consommation d'énergie primaire : {primary_energy} kWh/m²/an\n"
                f"Émissions de gaz à effet de serre : {emissions} kg CO2/m²/an\n"
                f"Classe énergétique : {rating}\n\n"
                "ESTIMATION DES COÛTS ANNUELS D'ÉNERGIE\n"
                "Montant estimé des dépenses annuelles d'énergie pour un usage standard : entre "
            )
            .entity(cost_min, EntityType.AMOUNT, "annual_cost_min", cost_min_norm)
            .text(" et ")
            .entity(cost_max, EntityType.AMOUNT, "annual_cost_max", cost_max_norm)
            .text(".\n\nÉtabli le ")
            .entity(issue, EntityType.DATE, "issue_date", issue_norm)
            .text(", valable jusqu'au ")
            .entity(expiry, EntityType.DATE, "expiry_date", expiry_norm)
            .text(".\n")
        )
