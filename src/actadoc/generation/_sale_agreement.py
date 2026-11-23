"""Generator of synthetic sale agreements (compromis de vente) for flats."""

from __future__ import annotations

import random
import string
from datetime import date, timedelta
from decimal import Decimal

from faker import Faker

from actadoc.generation._base import DocumentGenerator, register_generator
from actadoc.generation._builder import DocumentBuilder
from actadoc.generation._formats import (
    format_amount,
    format_cadastral_reference,
    format_date,
    format_surface,
)
from actadoc.generation._schema import DocumentType, EntityType

# Range of signature dates, fixed so that the corpus does not depend on the run date.
_FIRST_SIGNATURE = date(2024, 1, 1)
_SIGNATURE_SPAN_DAYS = 900
# Delay between the agreement and the authentic deed, in days (usually two to four months).
_DEED_DELAY_DAYS = (60, 121)

_LOAN_CONTINGENCIES = (
    "La présente vente est conclue sous la condition suspensive de l'obtention par "
    "l'acquéreur d'un ou plusieurs prêts dans un délai de quarante-cinq jours ; à défaut, "
    "le présent compromis sera caduc et le dépôt de garantie restitué à l'acquéreur.",
    "Les présentes sont soumises à la condition suspensive de l'obtention d'un financement "
    "bancaire par l'acquéreur ; si cette condition n'est pas réalisée dans le délai de "
    "soixante jours, chacune des parties sera libérée de ses engagements.",
)


@register_generator(DocumentType.SALE_AGREEMENT)
class SaleAgreementGenerator(DocumentGenerator):
    """Generate sale agreements for a flat in a co-ownership building.

    Entities produced, in reading order: seller and buyer (``party``),
    cadastral reference (``cadastral_reference``), Carrez living area
    (``surface``), price and deposit (``amount``), loan contingency clause
    (``termination_clause``), deed deadline and signature date (``date``).

    The deposit is 5 % to 10 % of the price, the usual range. The authentic
    deed must be signed 60 to 120 days after the agreement.

    Parameters
    ----------
    locale : str, default="fr_FR"
        Faker locale used for names and addresses.

    Notes
    -----
    The loan contingency is a *condition suspensive*: if it fails, the sale
    never takes effect. It is labelled ``termination_clause`` because, like a
    termination clause, it is the clause that makes the contract fall; the
    distinction is documented in ``LIMITATIONS.md``.
    """

    def _compose(self, builder: DocumentBuilder, fake: Faker, rng: random.Random) -> None:
        """Write a sale agreement into ``builder``."""
        seller = fake.name()
        buyer = fake.name()
        while buyer == seller:
            buyer = fake.name()
        address = fake.address().replace("\n", ", ")

        section = "".join(rng.choices(string.ascii_uppercase, k=rng.choice((1, 2))))
        cadastre, cadastre_norm = format_cadastral_reference(section, rng.randrange(1, 10000))
        surface, surface_norm = format_surface(Decimal(rng.randrange(150, 1500)) / 10)
        price_value = Decimal(rng.randrange(80, 901) * 1000)
        price, price_norm = format_amount(price_value)
        deposit, deposit_norm = format_amount(price_value * rng.randrange(5, 11) / 100)

        signed_on = _FIRST_SIGNATURE + timedelta(days=rng.randrange(_SIGNATURE_SPAN_DAYS))
        deed_by = signed_on + timedelta(days=rng.randrange(*_DEED_DELAY_DAYS))
        signature, signature_norm = format_date(signed_on)
        deadline, deadline_norm = format_date(deed_by)

        (
            builder.text(
                "COMPROMIS DE VENTE\n"
                "Lot de copropriété à usage d'habitation\n\n"
                "I. DÉSIGNATION DES PARTIES\n"
                "Entre les soussignés :\n- "
            )
            .entity(seller, EntityType.PARTY, "seller")
            .text(", ci-après dénommé(e) « le vendeur » ;\n- ")
            .entity(buyer, EntityType.PARTY, "buyer")
            .text(
                ", ci-après dénommé(e) « l'acquéreur ».\n\n"
                "II. DÉSIGNATION DU BIEN\n"
                f"Un appartement situé {address}, figurant au cadastre "
            )
            .entity(cadastre, EntityType.CADASTRAL_REFERENCE, "cadastral_reference", cadastre_norm)
            .text(
                ".\nSuperficie de la partie privative (loi n° 96-1107 du 18 décembre 1996, "
                "dite loi Carrez) : "
            )
            .entity(surface, EntityType.SURFACE, "living_area", surface_norm)
            .text(".\n\nIII. PRIX\nLa vente est consentie et acceptée moyennant le prix de ")
            .entity(price, EntityType.AMOUNT, "price", price_norm)
            .text(".\n\nIV. DÉPÔT DE GARANTIE\nL'acquéreur verse ce jour la somme de ")
            .entity(deposit, EntityType.AMOUNT, "deposit", deposit_norm)
            .text(", qui s'imputera sur le prix.\n\nV. CONDITION SUSPENSIVE\n")
            .entity(
                rng.choice(_LOAN_CONTINGENCIES), EntityType.TERMINATION_CLAUSE, "loan_contingency"
            )
            .text("\n\nVI. RÉITÉRATION\nL'acte authentique sera signé au plus tard le ")
            .entity(deadline, EntityType.DATE, "deed_deadline", deadline_norm)
            .text(".\n\nFait le ")
            .entity(signature, EntityType.DATE, "signature_date", signature_norm)
            .text(", en deux exemplaires originaux.\n")
        )
