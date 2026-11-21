"""Builder that assembles a document text and records entity spans as it goes."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, model_validator

from actadoc.generation._schema import DocumentType, Entity, EntityType, GroundTruth


class GeneratedDocument(BaseModel):
    """A generated document: its text and its ground truth.

    Parameters
    ----------
    text : str
        Full text of the document.
    ground_truth : GroundTruth
        Labelled entities of the document.

    Raises
    ------
    pydantic.ValidationError
        If an entity of ``ground_truth`` does not match its span in ``text``.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    text: str
    ground_truth: GroundTruth

    @model_validator(mode="after")
    def _check_spans(self) -> GeneratedDocument:
        """Check that every entity matches the text."""
        self.ground_truth.check_against(self.text)
        return self


class DocumentBuilder:
    """Assemble a document piece by piece, computing entity offsets automatically.

    Plain text is added with :meth:`text`, labelled values with :meth:`entity`.
    Offsets are computed from the current length of the document, so the span
    of an entity always matches its value: offsets are never counted by hand.

    Examples
    --------
    >>> builder = DocumentBuilder()
    >>> doc = (
    ...     builder.text("Loyer : ")
    ...     .entity("850,00 €", EntityType.AMOUNT, "rent", normalized="850.00")
    ...     .text(".")
    ...     .build(doc_id="lease-00000", doc_type=DocumentType.LEASE, seed=1)
    ... )
    >>> doc.text
    'Loyer : 850,00 €.'
    >>> doc.ground_truth.entities[0].start
    8
    """

    def __init__(self) -> None:
        self._parts: list[str] = []
        self._length = 0
        self._entities: list[Entity] = []

    def text(self, value: str) -> DocumentBuilder:
        """Append unlabelled text.

        Parameters
        ----------
        value : str
            Text to append.

        Returns
        -------
        DocumentBuilder
            The builder itself, so that calls can be chained.
        """
        self._parts.append(value)
        self._length += len(value)
        return self

    def entity(
        self,
        value: str,
        label: EntityType,
        role: str,
        normalized: str | None = None,
    ) -> DocumentBuilder:
        """Append a labelled value and record its span.

        Parameters
        ----------
        value : str
            Text of the entity, appended as is.
        label : EntityType
            Entity type.
        role : str
            Precise role of the entity, e.g. ``"landlord"``.
        normalized : str or None, default=None
            Canonical form of the value.

        Returns
        -------
        DocumentBuilder
            The builder itself, so that calls can be chained.

        Raises
        ------
        pydantic.ValidationError
            If ``value`` or ``role`` is empty.
        """
        start = self._length
        self._entities.append(
            Entity(
                label=label,
                role=role,
                value=value,
                normalized=normalized,
                start=start,
                end=start + len(value),
            )
        )
        return self.text(value)

    def build(self, doc_id: str, doc_type: DocumentType, seed: int) -> GeneratedDocument:
        """Return the assembled document with its ground truth.

        Parameters
        ----------
        doc_id : str
            Identifier of the document.
        doc_type : DocumentType
            Type of the document.
        seed : int
            Seed the document was generated from.

        Returns
        -------
        GeneratedDocument
            Text and validated ground truth.
        """
        ground_truth = GroundTruth(
            doc_id=doc_id, doc_type=doc_type, seed=seed, entities=list(self._entities)
        )
        return GeneratedDocument(text="".join(self._parts), ground_truth=ground_truth)
