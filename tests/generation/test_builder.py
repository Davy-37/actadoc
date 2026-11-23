"""Document builder: spans are computed, never counted by hand."""

import pytest
from pydantic import ValidationError

from actadoc.generation import DocumentBuilder, DocumentType, EntityType, GeneratedDocument


def build(builder):
    return builder.build(doc_id="lease-00000", doc_type=DocumentType.LEASE, seed=0)


def test_entity_offsets_follow_previous_text():
    doc = build(
        DocumentBuilder()
        .text("Bail entre ")
        .entity("Jean Dupont", EntityType.PARTY, "landlord")
        .text(" et ")
        .entity("Marie Martin", EntityType.PARTY, "tenant")
    )
    assert doc.text == "Bail entre Jean Dupont et Marie Martin"
    for entity in doc.ground_truth.entities:
        assert doc.text[entity.start : entity.end] == entity.value


def test_entity_at_document_start():
    doc = build(DocumentBuilder().entity("Jean", EntityType.PARTY, "landlord"))
    assert doc.ground_truth.entities[0].start == 0


def test_empty_builder_gives_empty_document():
    doc = build(DocumentBuilder())
    assert doc.text == ""
    assert doc.ground_truth.entities == []


def test_text_with_accents_and_symbols_keeps_offsets_right():
    doc = build(
        DocumentBuilder()
        .text("Dépôt de garantie « réglé » : ")
        .entity("1 250,00 €", EntityType.AMOUNT, "security_deposit", "1250.00")
    )
    entity = doc.ground_truth.entities[0]
    assert doc.text[entity.start : entity.end] == "1 250,00 €"


def test_empty_entity_value_is_rejected():
    with pytest.raises(ValidationError):
        DocumentBuilder().entity("", EntityType.PARTY, "landlord")


def test_generated_document_rejects_mismatching_text():
    doc = build(DocumentBuilder().text("Bail : ").entity("Jean", EntityType.PARTY, "landlord"))
    with pytest.raises(ValidationError):
        GeneratedDocument(text="Bail : Paul", ground_truth=doc.ground_truth)
