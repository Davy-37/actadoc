"""Ground-truth schema of generated documents."""

import pytest
from pydantic import ValidationError

from actadoc.generation import DocumentType, Entity, EntityType, GroundTruth

TEXT = "Bail entre Jean Dupont et Marie Martin. Loyer : 850,00 euros."


def entity(role, value, start, label=EntityType.PARTY, normalized=None):
    return Entity(
        label=label,
        role=role,
        value=value,
        normalized=normalized,
        start=start,
        end=start + len(value),
    )


@pytest.fixture
def entities():
    return [
        entity("landlord", "Jean Dupont", TEXT.index("Jean")),
        entity("tenant", "Marie Martin", TEXT.index("Marie")),
        entity("rent", "850,00 euros", TEXT.index("850"), EntityType.AMOUNT, "850.00"),
    ]


def ground_truth(entities):
    return GroundTruth(doc_id="lease-0001", doc_type=DocumentType.LEASE, seed=42, entities=entities)


def test_valid_ground_truth_matches_text(entities):
    ground_truth(entities).check_against(TEXT)


def test_ground_truth_round_trips_through_json(entities):
    gt = ground_truth(entities)
    assert GroundTruth.model_validate_json(gt.model_dump_json()) == gt


def test_document_without_entities_is_valid():
    ground_truth([]).check_against("")


@pytest.mark.parametrize(
    ("start", "end", "value"),
    [
        (-1, 4, "Jean"),  # negative start
        (11, 13, "Jean"),  # span shorter than value
        (11, 20, "Jean"),  # span longer than value
        (11, 11, ""),  # empty value
    ],
)
def test_invalid_entity_span_is_rejected(start, end, value):
    with pytest.raises(ValidationError):
        Entity(label=EntityType.PARTY, role="landlord", value=value, start=start, end=end)


def test_unknown_field_is_rejected():
    with pytest.raises(ValidationError):
        Entity(label="party", role="landlord", value="Jean", start=0, end=4, extra="x")


def test_unknown_entity_type_is_rejected():
    with pytest.raises(ValidationError):
        Entity(label="phone_number", role="landlord", value="Jean", start=0, end=4)


def test_negative_seed_is_rejected(entities):
    with pytest.raises(ValidationError):
        GroundTruth(doc_id="lease-0001", doc_type="lease", seed=-1, entities=entities)


def test_overlapping_entities_are_rejected(entities):
    overlapping = entity("landlord_last_name", "Dupont", TEXT.index("Dupont"))
    with pytest.raises(ValidationError):
        ground_truth([entities[0], overlapping])


def test_unsorted_entities_are_rejected(entities):
    with pytest.raises(ValidationError):
        ground_truth([entities[1], entities[0]])


def test_wrong_value_in_text_is_detected(entities):
    gt = ground_truth(entities)
    with pytest.raises(ValueError, match="expects 'Jean Dupont'"):
        gt.check_against(TEXT.replace("Jean Dupont", "Paul Durand"))


def test_span_beyond_text_is_detected(entities):
    gt = ground_truth(entities)
    with pytest.raises(ValueError, match="beyond the text length"):
        gt.check_against(TEXT[:20])


def test_ground_truth_is_immutable(entities):
    gt = ground_truth(entities)
    with pytest.raises(ValidationError):
        gt.seed = 7
