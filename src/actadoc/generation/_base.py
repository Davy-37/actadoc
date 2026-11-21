"""Common skeleton of document generators, registry and corpus generation."""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import ClassVar

from faker import Faker

from actadoc.generation._builder import DocumentBuilder, GeneratedDocument
from actadoc.generation._schema import DocumentType


class DocumentGenerator(ABC):
    """Base class of every document generator.

    :meth:`generate` fixes the steps shared by all document types (seeding,
    building, validation); subclasses only implement :meth:`_compose`, which
    writes the content of their document type.

    Parameters
    ----------
    locale : str, default="fr_FR"
        Faker locale used for names and addresses.

    Attributes
    ----------
    doc_type : DocumentType
        Type of document produced, set by each subclass.
    """

    doc_type: ClassVar[DocumentType]

    def __init__(self, locale: str = "fr_FR") -> None:
        self.locale = locale

    def generate(self, doc_id: str, seed: int) -> GeneratedDocument:
        """Generate one document, fully determined by ``seed``.

        Parameters
        ----------
        doc_id : str
            Identifier of the document.
        seed : int
            Seed of this document; the same seed always gives the same document.

        Returns
        -------
        GeneratedDocument
            Text and validated ground truth.
        """
        fake = Faker(self.locale)
        fake.seed_instance(seed)
        rng = random.Random(seed)
        builder = DocumentBuilder()
        self._compose(builder, fake, rng)
        return builder.build(doc_id=doc_id, doc_type=self.doc_type, seed=seed)

    @abstractmethod
    def _compose(self, builder: DocumentBuilder, fake: Faker, rng: random.Random) -> None:
        """Write the content of the document into ``builder``.

        Parameters
        ----------
        builder : DocumentBuilder
            Builder receiving text and entities, in reading order.
        fake : faker.Faker
            Seeded Faker instance for names and addresses.
        rng : random.Random
            Seeded random generator for numbers and choices.
        """


_REGISTRY: dict[DocumentType, type[DocumentGenerator]] = {}


def register_generator(
    doc_type: DocumentType,
) -> Callable[[type[DocumentGenerator]], type[DocumentGenerator]]:
    """Register a generator class for a document type (class decorator).

    Parameters
    ----------
    doc_type : DocumentType
        Document type produced by the decorated class.

    Returns
    -------
    callable
        Decorator that registers the class and returns it unchanged.

    Raises
    ------
    ValueError
        If a generator is already registered for ``doc_type``.
    """

    def decorator(cls: type[DocumentGenerator]) -> type[DocumentGenerator]:
        if doc_type in _REGISTRY:
            raise ValueError(f"a generator is already registered for {doc_type.value!r}")
        cls.doc_type = doc_type
        _REGISTRY[doc_type] = cls
        return cls

    return decorator


def get_generator(doc_type: DocumentType, locale: str = "fr_FR") -> DocumentGenerator:
    """Return a generator instance for a document type.

    Parameters
    ----------
    doc_type : DocumentType
        Requested document type.
    locale : str, default="fr_FR"
        Faker locale.

    Returns
    -------
    DocumentGenerator
        Generator of the requested type.

    Raises
    ------
    ValueError
        If no generator is registered for ``doc_type``.
    """
    try:
        cls = _REGISTRY[DocumentType(doc_type)]
    except KeyError:
        available = ", ".join(sorted(t.value for t in _REGISTRY)) or "none"
        raise ValueError(f"no generator for {doc_type!r}; available: {available}") from None
    return cls(locale=locale)


def document_seed(doc_type: DocumentType, corpus_seed: int, index: int) -> int:
    """Derive the seed of one document from the corpus seed.

    Each document gets its own seed, so that any document can be regenerated
    alone, and changing the number of documents does not change the others.

    Parameters
    ----------
    doc_type : DocumentType
        Document type, so that types with the same corpus seed differ.
    corpus_seed : int
        Seed of the whole corpus.
    index : int
        Position of the document in the corpus.

    Returns
    -------
    int
        Seed of the document, in ``[0, 2**32)``.
    """
    return random.Random(f"{DocumentType(doc_type).value}:{corpus_seed}:{index}").getrandbits(32)


def generate_documents(
    doc_type: DocumentType, n: int, seed: int, locale: str = "fr_FR"
) -> list[GeneratedDocument]:
    """Generate ``n`` documents of one type, reproducibly from ``seed``.

    Parameters
    ----------
    doc_type : DocumentType
        Type of the documents.
    n : int
        Number of documents, ``>= 0``.
    seed : int
        Corpus seed, ``>= 0``. The same seed always gives the same documents.
    locale : str, default="fr_FR"
        Faker locale.

    Returns
    -------
    list of GeneratedDocument
        Documents with identifiers ``"<type>-00000"``, ``"<type>-00001"``, ...

    Raises
    ------
    ValueError
        If ``n`` or ``seed`` is not a non-negative integer, or no generator is
        registered for ``doc_type``.

    Examples
    --------
    >>> docs = generate_documents(DocumentType.LEASE, n=2, seed=42)
    >>> [d.ground_truth.doc_id for d in docs]
    ['lease-00000', 'lease-00001']
    """
    for name, value in (("n", n), ("seed", seed)):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{name} must be a non-negative integer, got {value!r}")
    generator = get_generator(doc_type, locale=locale)
    return [
        generator.generate(
            doc_id=f"{generator.doc_type.value}-{index:05d}",
            seed=document_seed(generator.doc_type, seed, index),
        )
        for index in range(n)
    ]
