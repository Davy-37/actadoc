"""Reproducible generation of synthetic sale agreements."""

import random
import re
from collections import Counter
from datetime import date
from decimal import Decimal

import pytest

from actadoc.generation import (
    DocumentBuilder,
    DocumentType,
    EntityType,
    SaleAgreementGenerator,
    document_seed,
    generate_documents,
    get_generator,
)

EXPECTED_ROLES = [
    "seller",
    "buyer",
    "cadastral_reference",
    "living_area",
    "price",
    "deposit",
    "loan_contingency",
    "deed_deadline",
    "signature_date",
]


@pytest.fixture(scope="module")
def agreements():
    return generate_documents(DocumentType.SALE_AGREEMENT, n=50, seed=42)


def by_role(doc):
    return {e.role: e for e in doc.ground_truth.entities}


def test_same_seed_gives_identical_documents(agreements):
    again = generate_documents(DocumentType.SALE_AGREEMENT, n=50, seed=42)
    assert [d.model_dump_json() for d in again] == [d.model_dump_json() for d in agreements]


def test_different_seeds_give_different_documents(agreements):
    other = generate_documents(DocumentType.SALE_AGREEMENT, n=50, seed=43)
    assert [d.text for d in other] != [d.text for d in agreements]


def test_documents_within_a_corpus_are_distinct(agreements):
    assert len({d.text for d in agreements}) == len(agreements)


def test_a_document_can_be_regenerated_alone(agreements):
    doc = agreements[3]
    alone = SaleAgreementGenerator().generate(doc.ground_truth.doc_id, doc.ground_truth.seed)
    assert alone == doc
    assert doc.ground_truth.seed == document_seed(DocumentType.SALE_AGREEMENT, 42, 3)


def test_lease_and_sale_agreement_seeds_differ():
    assert document_seed(DocumentType.SALE_AGREEMENT, 42, 0) != document_seed(
        DocumentType.LEASE, 42, 0
    )


def test_every_agreement_has_the_expected_entities_in_order(agreements):
    for doc in agreements:
        assert [e.role for e in doc.ground_truth.entities] == EXPECTED_ROLES
        assert doc.ground_truth.doc_type is DocumentType.SALE_AGREEMENT


def test_every_entity_matches_its_span(agreements):
    for doc in agreements:
        doc.ground_truth.check_against(doc.text)


def test_entity_types_per_agreement(agreements):
    counts = Counter(e.label for e in agreements[0].ground_truth.entities)
    assert counts == {
        EntityType.PARTY: 2,
        EntityType.CADASTRAL_REFERENCE: 1,
        EntityType.SURFACE: 1,
        EntityType.AMOUNT: 2,
        EntityType.TERMINATION_CLAUSE: 1,
        EntityType.DATE: 2,
    }


def test_business_rules_hold(agreements):
    for doc in agreements:
        roles = by_role(doc)
        assert roles["seller"].value != roles["buyer"].value
        price = Decimal(roles["price"].normalized)
        assert 80_000 <= price <= 900_000
        assert price % 1000 == 0
        assert Decimal("0.05") * price <= Decimal(roles["deposit"].normalized) <= price / 10
        signed = date.fromisoformat(roles["signature_date"].normalized)
        deadline = date.fromisoformat(roles["deed_deadline"].normalized)
        assert 60 <= (deadline - signed).days <= 120
        assert Decimal(roles["living_area"].normalized) > 0


def test_cadastral_reference_is_normalized(agreements):
    for doc in agreements:
        assert re.fullmatch(r"[0A-Z][A-Z]\d{4}", by_role(doc)["cadastral_reference"].normalized)


def test_both_section_lengths_are_generated(agreements):
    lengths = {len(by_role(d)["cadastral_reference"].value.split()[1]) for d in agreements}
    assert lengths == {1, 2}


def test_identifiers_use_the_document_type():
    docs = generate_documents(DocumentType.SALE_AGREEMENT, n=2, seed=1)
    assert [d.ground_truth.doc_id for d in docs] == ["sale_agreement-00000", "sale_agreement-00001"]


def test_generator_is_registered():
    assert isinstance(get_generator("sale_agreement"), SaleAgreementGenerator)


class _SameNameFirst:
    """Faker stand-in that returns the same name twice before a different one."""

    def __init__(self):
        self._names = iter(["Jean Dupont", "Jean Dupont", "Marie Martin"])

    def name(self):
        return next(self._names)

    def address(self):
        return "1 rue de la Paix\n75002 Paris"


def test_buyer_name_is_redrawn_when_equal_to_seller():
    builder = DocumentBuilder()
    SaleAgreementGenerator()._compose(builder, _SameNameFirst(), random.Random(0))
    doc = builder.build(doc_id="sale_agreement-00000", doc_type=DocumentType.SALE_AGREEMENT, seed=0)
    roles = by_role(doc)
    assert (roles["seller"].value, roles["buyer"].value) == ("Jean Dupont", "Marie Martin")
