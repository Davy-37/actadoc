"""Ground-truth schema shared by every synthetic document type."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

SCHEMA_VERSION = "1.0"


class DocumentType(StrEnum):
    """Type of a generated document."""

    LEASE = "lease"
    SALE_AGREEMENT = "sale_agreement"
    ENERGY_CERTIFICATE = "energy_certificate"


class EntityType(StrEnum):
    """The six entity types extracted by ACTADOC."""

    PARTY = "party"
    AMOUNT = "amount"
    DATE = "date"
    CADASTRAL_REFERENCE = "cadastral_reference"
    SURFACE = "surface"
    TERMINATION_CLAUSE = "termination_clause"


class Entity(BaseModel):
    """One labelled span of a generated document.

    Parameters
    ----------
    label : EntityType
        Entity type, one of the six types extracted by ACTADOC.
    role : str
        Precise role of the entity in the document, e.g. ``"landlord"``,
        ``"rent"`` or ``"start_date"``.
    value : str
        Exact text of the entity as it appears in the document.
    normalized : str or None, default=None
        Canonical form of the value, e.g. an ISO 8601 date or a decimal
        amount, used to compare extractions that differ only in formatting.
    start : int
        Offset of the first character of the entity in the document text.
    end : int
        Offset one past the last character, so that ``text[start:end] == value``.

    Raises
    ------
    pydantic.ValidationError
        If ``start`` is negative, ``value`` is empty, or ``end - start``
        differs from the length of ``value``.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    label: EntityType
    role: str = Field(min_length=1)
    value: str = Field(min_length=1)
    normalized: str | None = None
    start: int = Field(ge=0)
    end: int

    @model_validator(mode="after")
    def _check_span(self) -> Entity:
        """Check that the span length matches the value length."""
        if self.end - self.start != len(self.value):
            raise ValueError(
                f"span [{self.start}, {self.end}) has length {self.end - self.start}, "
                f"but value has length {len(self.value)}"
            )
        return self


class GroundTruth(BaseModel):
    """Ground truth of one generated document.

    Parameters
    ----------
    doc_id : str
        Unique identifier of the document within the corpus.
    doc_type : DocumentType
        Type of the document.
    seed : int
        Seed used to generate this document, so that it can be regenerated.
    entities : list of Entity
        Labelled spans, sorted by ``start`` and non-overlapping.
    schema_version : str, default=SCHEMA_VERSION
        Version of this schema, bumped when its structure changes.

    Raises
    ------
    pydantic.ValidationError
        If ``seed`` is negative, or entities are unsorted or overlapping.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    doc_id: str = Field(min_length=1)
    doc_type: DocumentType
    seed: int = Field(ge=0)
    entities: list[Entity]
    schema_version: str = SCHEMA_VERSION

    @model_validator(mode="after")
    def _check_order(self) -> GroundTruth:
        """Check that entities are sorted and do not overlap."""
        for previous, current in zip(self.entities, self.entities[1:], strict=False):
            if current.start < previous.end:
                raise ValueError(
                    f"entity '{current.role}' at {current.start} starts before "
                    f"the end of entity '{previous.role}' at {previous.end}"
                )
        return self

    def check_against(self, text: str) -> None:
        """Check that every entity matches its span in the document text.

        Parameters
        ----------
        text : str
            Full text of the document this ground truth describes.

        Raises
        ------
        ValueError
            If an entity span lies outside ``text`` or ``text[start:end]``
            differs from the entity value.
        """
        for entity in self.entities:
            if entity.end > len(text):
                raise ValueError(
                    f"entity '{entity.role}' ends at {entity.end}, "
                    f"beyond the text length {len(text)}"
                )
            found = text[entity.start : entity.end]
            if found != entity.value:
                raise ValueError(
                    f"entity '{entity.role}' expects {entity.value!r} "
                    f"at [{entity.start}, {entity.end}), found {found!r}"
                )
