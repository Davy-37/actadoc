"""Reproducible generation of synthetic energy performance certificates."""

import random
import re
from collections import Counter
from datetime import date
from decimal import Decimal

import pytest

from actadoc.generation import (
    DocumentBuilder,
    DocumentType,
    EnergyCertificateGenerator,
    EntityType,
    document_seed,
    energy_class,
    generate_documents,
    get_generator,
)
from actadoc.generation._energy_certificate import _add_years, _round_to_ten

EXPECTED_ROLES = [
    "owner",
    "diagnostician",
    "living_area",
    "annual_cost_min",
    "annual_cost_max",
    "issue_date",
    "expiry_date",
]


@pytest.fixture(scope="module")
def certificates():
    return generate_documents(DocumentType.ENERGY_CERTIFICATE, n=50, seed=42)


def by_role(doc):
    return {e.role: e for e in doc.ground_truth.entities}


def test_same_seed_gives_identical_documents(certificates):
    again = generate_documents(DocumentType.ENERGY_CERTIFICATE, n=50, seed=42)
    assert [d.model_dump_json() for d in again] == [d.model_dump_json() for d in certificates]


def test_different_seeds_give_different_documents(certificates):
    other = generate_documents(DocumentType.ENERGY_CERTIFICATE, n=50, seed=43)
    assert [d.text for d in other] != [d.text for d in certificates]


def test_documents_within_a_corpus_are_distinct(certificates):
    assert len({d.text for d in certificates}) == len(certificates)


def test_a_document_can_be_regenerated_alone(certificates):
    doc = certificates[5]
    alone = EnergyCertificateGenerator().generate(doc.ground_truth.doc_id, doc.ground_truth.seed)
    assert alone == doc
    assert doc.ground_truth.seed == document_seed(DocumentType.ENERGY_CERTIFICATE, 42, 5)


def test_every_certificate_has_the_expected_entities_in_order(certificates):
    for doc in certificates:
        assert [e.role for e in doc.ground_truth.entities] == EXPECTED_ROLES
        assert doc.ground_truth.doc_type is DocumentType.ENERGY_CERTIFICATE


def test_every_entity_matches_its_span(certificates):
    for doc in certificates:
        doc.ground_truth.check_against(doc.text)


def test_entity_types_per_certificate(certificates):
    counts = Counter(e.label for e in certificates[0].ground_truth.entities)
    assert counts == {
        EntityType.PARTY: 2,
        EntityType.SURFACE: 1,
        EntityType.AMOUNT: 2,
        EntityType.DATE: 2,
    }


def test_business_rules_hold(certificates):
    for doc in certificates:
        roles = by_role(doc)
        assert roles["owner"].value != roles["diagnostician"].value
        assert (
            0
            < Decimal(roles["annual_cost_min"].normalized)
            < Decimal(roles["annual_cost_max"].normalized)
        )
        issued = date.fromisoformat(roles["issue_date"].normalized)
        expires = date.fromisoformat(roles["expiry_date"].normalized)
        assert expires == _add_years(issued, 10)


def test_stated_class_matches_stated_values(certificates):
    pattern = re.compile(
        r"énergie primaire : (\d+) kWh.*?effet de serre : (\d+) kg.*?Classe énergétique : ([A-G])",
        re.DOTALL,
    )
    classes = set()
    for doc in certificates:
        primary_energy, emissions, stated = pattern.search(doc.text).groups()
        assert stated == energy_class(Decimal(primary_energy), Decimal(emissions))
        classes.add(stated)
    assert len(classes) >= 4  # the corpus covers several classes, not a single one


@pytest.mark.parametrize(
    ("day", "expected"),
    [
        (date(2025, 3, 14), date(2035, 3, 14)),
        (date(2024, 2, 29), date(2034, 2, 28)),  # leap day
    ],
)
def test_add_years(day, expected):
    assert _add_years(day, 10) == expected


@pytest.mark.parametrize(
    ("amount", "expected"),
    [(Decimal("1234"), Decimal("1230")), (Decimal("1235"), Decimal("1240")), (Decimal("4"), 0)],
)
def test_round_to_ten(amount, expected):
    assert _round_to_ten(amount) == expected


def test_generator_is_registered():
    assert isinstance(get_generator("energy_certificate"), EnergyCertificateGenerator)


class _SameNameFirst:
    """Faker stand-in that returns the same name twice before a different one."""

    def __init__(self):
        self._names = iter(["Jean Dupont", "Jean Dupont", "Marie Martin"])

    def name(self):
        return next(self._names)

    def company(self):
        return "Diag Conseil"

    def address(self):
        return "1 rue de la Paix\n75002 Paris"


def test_diagnostician_name_is_redrawn_when_equal_to_owner():
    builder = DocumentBuilder()
    EnergyCertificateGenerator()._compose(builder, _SameNameFirst(), random.Random(0))
    doc = builder.build(
        doc_id="energy_certificate-00000", doc_type=DocumentType.ENERGY_CERTIFICATE, seed=0
    )
    roles = by_role(doc)
    assert (roles["owner"].value, roles["diagnostician"].value) == ("Jean Dupont", "Marie Martin")
