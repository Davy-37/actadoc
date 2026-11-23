"""Reproducible generation of synthetic leases."""

from collections import Counter
from datetime import date
from decimal import Decimal

import pytest

from actadoc.generation import (
    DocumentGenerator,
    DocumentType,
    EntityType,
    LeaseGenerator,
    document_seed,
    generate_documents,
    get_generator,
    register_generator,
)

EXPECTED_ROLES = [
    "landlord",
    "tenant",
    "living_area",
    "start_date",
    "rent",
    "service_charges",
    "security_deposit",
    "termination",
    "signature_date",
]


@pytest.fixture(scope="module")
def leases():
    return generate_documents(DocumentType.LEASE, n=50, seed=42)


def by_role(doc):
    return {e.role: e for e in doc.ground_truth.entities}


def test_same_seed_gives_identical_documents(leases):
    again = generate_documents(DocumentType.LEASE, n=50, seed=42)
    assert [d.model_dump_json() for d in again] == [d.model_dump_json() for d in leases]


def test_different_seeds_give_different_documents(leases):
    other = generate_documents(DocumentType.LEASE, n=50, seed=43)
    assert [d.text for d in other] != [d.text for d in leases]


def test_documents_within_a_corpus_are_distinct(leases):
    assert len({d.text for d in leases}) == len(leases)


def test_a_document_does_not_depend_on_corpus_size(leases):
    shorter = generate_documents(DocumentType.LEASE, n=5, seed=42)
    assert [d.text for d in shorter] == [d.text for d in leases[:5]]


def test_a_document_can_be_regenerated_alone(leases):
    doc = leases[7]
    alone = LeaseGenerator().generate(doc.ground_truth.doc_id, doc.ground_truth.seed)
    assert alone == doc
    assert doc.ground_truth.seed == document_seed(DocumentType.LEASE, 42, 7)


def test_every_lease_has_the_expected_entities_in_order(leases):
    for doc in leases:
        assert [e.role for e in doc.ground_truth.entities] == EXPECTED_ROLES
        assert doc.ground_truth.doc_type is DocumentType.LEASE


def test_every_entity_matches_its_span(leases):
    for doc in leases:
        doc.ground_truth.check_against(doc.text)


def test_entity_types_per_lease(leases):
    counts = Counter(e.label for e in leases[0].ground_truth.entities)
    assert counts == {
        EntityType.PARTY: 2,
        EntityType.SURFACE: 1,
        EntityType.DATE: 2,
        EntityType.AMOUNT: 3,
        EntityType.TERMINATION_CLAUSE: 1,
    }


def test_business_rules_hold(leases):
    for doc in leases:
        roles = by_role(doc)
        assert roles["landlord"].value != roles["tenant"].value
        assert roles["security_deposit"].normalized == roles["rent"].normalized
        assert date.fromisoformat(roles["start_date"].normalized) > date.fromisoformat(
            roles["signature_date"].normalized
        )
        assert Decimal(roles["living_area"].normalized) > 0


def test_identifiers_are_sequential(leases):
    assert [d.ground_truth.doc_id for d in leases[:3]] == [
        "lease-00000",
        "lease-00001",
        "lease-00002",
    ]


def test_zero_documents():
    assert generate_documents(DocumentType.LEASE, n=0, seed=1) == []


@pytest.mark.parametrize(
    ("n", "seed"),
    [(-1, 1), (1.5, 1), (True, 1), ("3", 1), (1, -1), (1, 2.0), (1, None)],
)
def test_invalid_n_or_seed_is_rejected(n, seed):
    with pytest.raises(ValueError, match="non-negative integer"):
        generate_documents(DocumentType.LEASE, n=n, seed=seed)


def test_document_type_can_be_given_as_string():
    assert isinstance(get_generator("lease"), LeaseGenerator)


def test_unregistered_document_type_is_rejected():
    with pytest.raises(ValueError, match="no generator"):
        get_generator(DocumentType.SALE_AGREEMENT)


def test_registering_a_type_twice_is_rejected():
    with pytest.raises(ValueError, match="already registered"):

        @register_generator(DocumentType.LEASE)
        class OtherLease(DocumentGenerator):
            def _compose(self, builder, fake, rng):
                pass


class _SameNameFirst:
    """Faker stand-in that returns the same name twice before a different one."""

    def __init__(self):
        self._names = iter(["Jean Dupont", "Jean Dupont", "Marie Martin"])

    def name(self):
        return next(self._names)

    def address(self):
        return "1 rue de la Paix\n75002 Paris"


def test_tenant_name_is_redrawn_when_equal_to_landlord():
    import random

    from actadoc.generation import DocumentBuilder

    builder = DocumentBuilder()
    LeaseGenerator()._compose(builder, _SameNameFirst(), random.Random(0))
    roles = by_role(builder.build(doc_id="lease-00000", doc_type=DocumentType.LEASE, seed=0))
    assert (roles["landlord"].value, roles["tenant"].value) == ("Jean Dupont", "Marie Martin")
