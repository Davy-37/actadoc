"""Synthetic corpus generation: templates, Faker values, PDF rendering, scan degradation.

Generate documents with :func:`generate_documents`; each result carries its
text and a validated :class:`GroundTruth`. New document types subclass
:class:`DocumentGenerator` and register with :func:`register_generator`.
"""

# Importing the concrete generators registers them.
from actadoc.generation import _energy_certificate, _lease, _sale_agreement  # noqa: F401
from actadoc.generation._base import (
    DocumentGenerator,
    document_seed,
    generate_documents,
    get_generator,
    register_generator,
)
from actadoc.generation._builder import DocumentBuilder, GeneratedDocument
from actadoc.generation._energy_certificate import EnergyCertificateGenerator
from actadoc.generation._energy_classes import ENERGY_CLASSES, energy_class
from actadoc.generation._io import write_corpus
from actadoc.generation._lease import LeaseGenerator
from actadoc.generation._render import render_pdf, to_html
from actadoc.generation._sale_agreement import SaleAgreementGenerator
from actadoc.generation._scan import (
    PROFILES,
    SCAN_SCHEMA_VERSION,
    ScanLevel,
    ScanProfile,
    ScanRecord,
    apply_operations,
    sample_operations,
)
from actadoc.generation._scanner import rasterize_pdf, scan_pdf
from actadoc.generation._schema import (
    SCHEMA_VERSION,
    DocumentType,
    Entity,
    EntityType,
    GroundTruth,
)
from actadoc.generation._stats import (
    OPERATION_NAMES,
    Summary,
    energy_class_counts,
    entity_counts,
    operation_rates,
    summarize,
    word_counts,
)

__all__ = [
    "ENERGY_CLASSES",
    "OPERATION_NAMES",
    "PROFILES",
    "SCAN_SCHEMA_VERSION",
    "SCHEMA_VERSION",
    "DocumentBuilder",
    "DocumentGenerator",
    "DocumentType",
    "EnergyCertificateGenerator",
    "Entity",
    "EntityType",
    "GeneratedDocument",
    "GroundTruth",
    "LeaseGenerator",
    "SaleAgreementGenerator",
    "ScanLevel",
    "ScanProfile",
    "ScanRecord",
    "Summary",
    "apply_operations",
    "document_seed",
    "energy_class",
    "energy_class_counts",
    "entity_counts",
    "generate_documents",
    "get_generator",
    "operation_rates",
    "rasterize_pdf",
    "register_generator",
    "render_pdf",
    "sample_operations",
    "scan_pdf",
    "summarize",
    "to_html",
    "word_counts",
    "write_corpus",
]
