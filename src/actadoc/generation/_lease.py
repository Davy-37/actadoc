"""Generator of synthetic residential leases (unfurnished main residence)."""

from __future__ import annotations

import random
from datetime import date, timedelta
from decimal import Decimal

from faker import Faker

from actadoc.generation._base import DocumentGenerator, register_generator
from actadoc.generation._builder import DocumentBuilder
from actadoc.generation._formats import format_amount, format_date, format_surface
from actadoc.generation._schema import DocumentType, EntityType

# Range of signature dates, fixed so that the corpus does not depend on the run date.
_FIRST_SIGNATURE = date(2024, 1, 1)
_SIGNATURE_SPAN_DAYS = 900

_TERMINATION_CLAUSES = (
    "Le présent contrat sera résilié de plein droit à défaut de paiement du loyer "
    "ou des charges aux termes convenus, six semaines après un commandement de payer "
    "demeuré infructueux.",
    "À défaut de paiement du loyer et des charges ou de versement du dépôt de garantie, "
    "le bail sera résilié de plein droit six semaines après un commandement de payer "
    "resté sans effet.",
)


@register_generator(DocumentType.LEASE)
class LeaseGenerator(DocumentGenerator):
    """Generate residential leases modelled on the standard unfurnished lease.

    Entities produced, in reading order: landlord and tenant (``party``),
    living area (``surface``), start date (``date``), rent, service charges and
    security deposit (``amount``), termination clause (``termination_clause``)
    and signature date (``date``).

    The security deposit equals one month of rent excluding charges, the legal
    maximum for an unfurnished lease. The start date follows the signature date.

    Parameters
    ----------
    locale : str, default="fr_FR"
        Faker locale used for names and addresses.
    """

    def _compose(self, builder: DocumentBuilder, fake: Faker, rng: random.Random) -> None:
        """Write a lease into ``builder``."""
        landlord = fake.name()
        tenant = fake.name()
        while tenant == landlord:
            tenant = fake.name()
        address = fake.address().replace("\n", ", ")

        surface, surface_norm = format_surface(Decimal(rng.randrange(180, 1400)) / 10)
        rent_value = Decimal(rng.randrange(450, 2500))
        rent, rent_norm = format_amount(rent_value)
        charges, charges_norm = format_amount(Decimal(rng.randrange(30, 250)))
        deposit, deposit_norm = format_amount(rent_value)

        signed_on = _FIRST_SIGNATURE + timedelta(days=rng.randrange(_SIGNATURE_SPAN_DAYS))
        starts_on = signed_on + timedelta(days=rng.randrange(1, 45))
        signature, signature_norm = format_date(signed_on)
        start, start_norm = format_date(starts_on)

        (
            builder.text(
                "CONTRAT DE LOCATION\n"
                "Logement nu à usage de résidence principale\n"
                "(soumis à la loi n° 89-462 du 6 juillet 1989)\n\n"
                "I. DÉSIGNATION DES PARTIES\n"
                "Le présent contrat est conclu entre les soussignés :\n- "
            )
            .entity(landlord, EntityType.PARTY, "landlord")
            .text(", ci-après dénommé(e) « le bailleur » ;\n- ")
            .entity(tenant, EntityType.PARTY, "tenant")
            .text(
                ", ci-après dénommé(e) « le locataire ».\n\n"
                "II. OBJET DU CONTRAT\n"
                f"Le présent contrat a pour objet la location d'un logement situé {address}, "
                "d'une surface habitable de "
            )
            .entity(surface, EntityType.SURFACE, "living_area", surface_norm)
            .text(".\n\nIII. DATE DE PRISE D'EFFET ET DURÉE\nLe contrat prend effet le ")
            .entity(start, EntityType.DATE, "start_date", start_norm)
            .text(
                " pour une durée de trois ans.\n\n"
                "IV. CONDITIONS FINANCIÈRES\n"
                "Le montant du loyer mensuel est fixé à "
            )
            .entity(rent, EntityType.AMOUNT, "rent", rent_norm)
            .text(", auquel s'ajoute une provision sur charges de ")
            .entity(charges, EntityType.AMOUNT, "service_charges", charges_norm)
            .text(".\n\nV. GARANTIES\nLe locataire verse un dépôt de garantie de ")
            .entity(deposit, EntityType.AMOUNT, "security_deposit", deposit_norm)
            .text(".\n\nVI. CLAUSE RÉSOLUTOIRE\n")
            .entity(rng.choice(_TERMINATION_CLAUSES), EntityType.TERMINATION_CLAUSE, "termination")
            .text("\n\nFait le ")
            .entity(signature, EntityType.DATE, "signature_date", signature_norm)
            .text(", en deux exemplaires originaux.\n")
        )
