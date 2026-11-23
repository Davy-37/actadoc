"""Statistics of a synthetic corpus, reported in ``METRICS.md``."""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

import numpy as np

from actadoc.generation._builder import GeneratedDocument
from actadoc.generation._scan import PROFILES, ScanLevel, sample_operations
from actadoc.generation._schema import EntityType

# Page shape used to draw operations. Which operations a page gets does not
# depend on the shape, only their parameters (stamp position, size) do.
_PAGE_SHAPE = (2339, 1654)  # A4 at 200 dpi

_ENERGY_CLASS = re.compile(r"Classe énergétique : ([A-G])")

# In the order they are applied; a test checks it against the operation models.
OPERATION_NAMES = ("rotate", "fold", "stamp", "lighting", "blur", "noise", "jpeg")


@dataclass(frozen=True)
class Summary:
    """Minimum, mean and maximum of a series of values.

    Parameters
    ----------
    minimum : float
        Smallest value.
    mean : float
        Arithmetic mean.
    maximum : float
        Largest value.
    """

    minimum: float
    mean: float
    maximum: float


def summarize(values: Sequence[float]) -> Summary:
    """Return the minimum, mean and maximum of ``values``.

    Parameters
    ----------
    values : sequence of float
        Values to summarize, at least one.

    Returns
    -------
    Summary
        Minimum, mean and maximum.

    Raises
    ------
    ValueError
        If ``values`` is empty.

    Examples
    --------
    >>> summarize([2, 4, 9])
    Summary(minimum=2, mean=5.0, maximum=9)
    """
    if not values:
        raise ValueError("cannot summarize an empty series")
    return Summary(min(values), sum(values) / len(values), max(values))


def entity_counts(documents: Iterable[GeneratedDocument]) -> dict[EntityType, int]:
    """Count the labelled entities of each type.

    Parameters
    ----------
    documents : iterable of GeneratedDocument
        Documents of the corpus.

    Returns
    -------
    dict
        Number of entities per type, for all six types (``0`` when absent),
        in the order of :class:`EntityType`.
    """
    counts = Counter(entity.label for doc in documents for entity in doc.ground_truth.entities)
    return {label: counts[label] for label in EntityType}


def word_counts(documents: Iterable[GeneratedDocument]) -> Summary:
    """Summarize the number of words per document.

    Parameters
    ----------
    documents : iterable of GeneratedDocument
        Documents of the corpus, at least one.

    Returns
    -------
    Summary
        Minimum, mean and maximum number of whitespace-separated words.
    """
    return summarize([len(doc.text.split()) for doc in documents])


def energy_class_counts(documents: Iterable[GeneratedDocument]) -> dict[str, int]:
    """Count the energy classes stated in energy performance certificates.

    The class is not a labelled entity, so it is read from the text. Documents
    without a stated class are ignored.

    Parameters
    ----------
    documents : iterable of GeneratedDocument
        Documents of the corpus.

    Returns
    -------
    dict
        Number of certificates per class, ``"A"`` to ``"G"``.
    """
    counts: Counter[str] = Counter()
    for doc in documents:
        match = _ENERGY_CLASS.search(doc.text)
        if match:
            counts[match.group(1)] += 1
    return {energy_class: counts[energy_class] for energy_class in "ABCDEFG"}


def operation_rates(
    pages_per_seed: Iterable[tuple[int, int]], level: ScanLevel
) -> dict[str, float]:
    """Share of scanned pages that get each degradation operation.

    Operations are drawn exactly as :func:`scan_pdf` draws them: one random
    generator per document, seeded with its seed, then one draw per page.

    Parameters
    ----------
    pages_per_seed : iterable of tuple of int
        ``(seed, number of pages)`` of each document.
    level : ScanLevel
        Degradation level.

    Returns
    -------
    dict
        Share of pages, from 0 to 1, for every operation name.

    Raises
    ------
    ValueError
        If there are no pages at all.
    """
    profile = PROFILES[ScanLevel(level)]
    counts: Counter[str] = Counter()
    total = 0
    for seed, n_pages in pages_per_seed:
        rng = np.random.default_rng(seed)
        for _ in range(n_pages):
            counts.update(op.name for op in sample_operations(profile, _PAGE_SHAPE, rng))
            total += 1
    if total == 0:
        raise ValueError("no pages to compute rates on")
    return {name: counts[name] / total for name in OPERATION_NAMES}
