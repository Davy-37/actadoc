"""Statistics of a synthetic corpus."""

from typing import get_args

import numpy as np
import pytest

from actadoc.generation import DocumentType, EntityType, ScanLevel, generate_documents
from actadoc.generation._scan import PROFILES, Operation, sample_operations
from actadoc.generation._stats import (
    OPERATION_NAMES,
    Summary,
    energy_class_counts,
    entity_counts,
    operation_rates,
    summarize,
    word_counts,
)


@pytest.fixture(scope="module")
def corpus():
    return {t: generate_documents(t, n=20, seed=42) for t in DocumentType}


def test_summarize():
    assert summarize([3]) == Summary(3, 3.0, 3)
    with pytest.raises(ValueError, match="empty"):
        summarize([])


def test_entity_counts_cover_the_six_types(corpus):
    counts = entity_counts(corpus[DocumentType.LEASE])
    assert list(counts) == list(EntityType)
    assert counts[EntityType.PARTY] == 2 * 20
    assert counts[EntityType.AMOUNT] == 3 * 20
    assert counts[EntityType.CADASTRAL_REFERENCE] == 0  # leases have none


def test_every_entity_type_appears_in_the_whole_corpus(corpus):
    everything = [doc for docs in corpus.values() for doc in docs]
    assert all(count > 0 for count in entity_counts(everything).values())


def test_word_counts(corpus):
    summary = word_counts(corpus[DocumentType.LEASE])
    assert 0 < summary.minimum <= summary.mean <= summary.maximum


def test_energy_classes_are_read_from_certificates_only(corpus):
    counts = energy_class_counts(corpus[DocumentType.ENERGY_CERTIFICATE])
    assert list(counts) == list("ABCDEFG")
    assert sum(counts.values()) == 20
    assert sum(energy_class_counts(corpus[DocumentType.LEASE]).values()) == 0


def test_operation_names_match_the_operation_models():
    models = get_args(get_args(Operation)[0])
    assert {model.model_fields["name"].default for model in models} == set(OPERATION_NAMES)


def test_clean_level_has_no_operation():
    assert set(operation_rates([(1, 2), (2, 1)], ScanLevel.CLEAN).values()) == {0.0}


def test_heavy_level_applies_everything_to_every_page():
    rates = operation_rates([(seed, 2) for seed in range(10)], ScanLevel.HEAVY)
    assert rates == {name: 1.0 for name in OPERATION_NAMES}


def test_rates_match_the_operations_drawn_by_a_scan():
    """Same draws as scan_pdf: one generator per document, one draw per page."""
    seeds = [(seed, 2) for seed in range(40)]
    stamped = 0
    for seed, pages in seeds:
        rng = np.random.default_rng(seed)
        for _ in range(pages):
            ops = sample_operations(PROFILES[ScanLevel.MEDIUM], (300, 200), rng)
            stamped += "stamp" in {op.name for op in ops}
    assert operation_rates(seeds, ScanLevel.MEDIUM)["stamp"] == stamped / 80


def test_rates_need_at_least_one_page():
    with pytest.raises(ValueError, match="no pages"):
        operation_rates([(1, 0)], ScanLevel.LIGHT)
