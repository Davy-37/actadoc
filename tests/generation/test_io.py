"""Writing generated documents to disk."""

import pytest

from actadoc.generation import DocumentType, GroundTruth, generate_documents, write_corpus


@pytest.fixture
def docs():
    return generate_documents(DocumentType.LEASE, n=3, seed=1)


def test_writes_text_and_ground_truth(tmp_path, docs):
    paths = write_corpus(docs, tmp_path / "leases")
    assert [p.name for p in paths[:2]] == ["lease-00000.txt", "lease-00000.json"]
    assert len(paths) == 6
    for doc in docs:
        stem = tmp_path / "leases" / doc.ground_truth.doc_id
        assert stem.with_suffix(".txt").read_text(encoding="utf-8") == doc.text
        loaded = GroundTruth.model_validate_json(
            stem.with_suffix(".json").read_text(encoding="utf-8")
        )
        assert loaded == doc.ground_truth
        loaded.check_against(doc.text)


def test_accents_are_written_as_utf8(tmp_path, docs):
    write_corpus(docs, tmp_path)
    raw = (tmp_path / "lease-00000.txt").read_bytes()
    assert "DÉSIGNATION".encode() in raw


def test_rewriting_is_idempotent(tmp_path, docs):
    write_corpus(docs, tmp_path)
    first = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    write_corpus(docs, tmp_path)
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == first


def test_no_documents_creates_empty_directory(tmp_path):
    assert write_corpus([], tmp_path / "empty") == []
    assert (tmp_path / "empty").is_dir()


def test_existing_file_as_output_is_rejected(tmp_path, docs):
    target = tmp_path / "not_a_dir"
    target.write_text("x")
    with pytest.raises(NotADirectoryError):
        write_corpus(docs, target)
