"""Scan simulation: levels, operation records and their application."""

import numpy as np
import pytest
from pydantic import ValidationError

from actadoc.generation._scan import (
    PROFILES,
    Blur,
    Jpeg,
    Noise,
    Rotate,
    ScanLevel,
    ScanRecord,
    Stamp,
    _Operation,
    apply_operations,
    sample_operations,
)

SHAPE = (300, 200)


@pytest.fixture
def page():
    image = np.full(SHAPE, 255, dtype=np.uint8)
    image[100:120, 30:170] = 0
    return image


def names(operations):
    return [op.name for op in operations]


def test_every_level_has_a_profile():
    assert set(PROFILES) == set(ScanLevel)


def test_clean_level_applies_nothing(page):
    operations = sample_operations(PROFILES[ScanLevel.CLEAN], SHAPE, np.random.default_rng(0))
    assert operations == []
    assert np.array_equal(apply_operations(page, operations), page)


def test_heavy_level_applies_every_operation_in_order():
    operations = sample_operations(PROFILES[ScanLevel.HEAVY], SHAPE, np.random.default_rng(0))
    assert names(operations) == ["rotate", "fold", "stamp", "lighting", "blur", "noise", "jpeg"]


def test_light_level_never_stamps_nor_folds():
    for seed in range(30):
        ops = sample_operations(PROFILES[ScanLevel.LIGHT], SHAPE, np.random.default_rng(seed))
        assert not {"stamp", "fold", "blur"} & set(names(ops))


def test_medium_level_sometimes_stamps():
    stamped = [
        "stamp"
        in names(sample_operations(PROFILES[ScanLevel.MEDIUM], SHAPE, np.random.default_rng(s)))
        for s in range(30)
    ]
    assert any(stamped) and not all(stamped)


@pytest.mark.parametrize("level", list(ScanLevel))
def test_sampled_parameters_stay_within_the_profile(level):
    profile = PROFILES[level]
    for seed in range(20):
        for op in sample_operations(profile, SHAPE, np.random.default_rng(seed)):
            if isinstance(op, Rotate):
                assert abs(op.angle) <= profile.max_rotation
            elif isinstance(op, Noise):
                assert profile.noise_sigma[0] <= op.sigma <= profile.noise_sigma[1]
            elif isinstance(op, Jpeg):
                assert profile.jpeg_quality[0] <= op.quality <= profile.jpeg_quality[1]
            elif isinstance(op, Blur):
                assert op.kernel in profile.blur_kernels
            elif isinstance(op, Stamp):
                x, y = op.centre
                assert op.radius <= x <= SHAPE[1] - op.radius
                assert op.radius <= y <= SHAPE[0] - op.radius


def test_heavier_levels_degrade_more(page):
    error = {}
    for level in ScanLevel:
        ops = sample_operations(PROFILES[level], SHAPE, np.random.default_rng(3))
        error[level] = np.abs(apply_operations(page, ops).astype(int) - page).mean()
    assert error[ScanLevel.CLEAN] == 0
    assert error[ScanLevel.LIGHT] < error[ScanLevel.MEDIUM] < error[ScanLevel.HEAVY]


def test_same_seed_gives_the_same_operations():
    profile = PROFILES[ScanLevel.HEAVY]
    first = sample_operations(profile, SHAPE, np.random.default_rng(7))
    assert sample_operations(profile, SHAPE, np.random.default_rng(7)) == first


def test_a_record_replays_the_same_page_after_a_json_round_trip(page):
    operations = sample_operations(PROFILES[ScanLevel.HEAVY], SHAPE, np.random.default_rng(5))
    record = ScanRecord(doc_id="lease-00000", level="heavy", seed=5, dpi=200, pages=[operations])
    restored = ScanRecord.model_validate_json(record.model_dump_json())
    assert restored == record
    assert isinstance(restored.pages[0][2], Stamp)  # read back as the right model
    assert np.array_equal(
        apply_operations(page, restored.pages[0]), apply_operations(page, operations)
    )


@pytest.mark.parametrize(
    "operation",
    [
        {"name": "jpeg", "quality": 0},
        {"name": "blur", "kernel": 0},
        {"name": "noise", "sigma": 5, "seed": -1},
        {"name": "rotate", "angle": 1, "extra": True},
        {"name": "warp", "angle": 1},
    ],
)
def test_invalid_operation_in_a_record_is_rejected(operation):
    with pytest.raises(ValidationError):
        ScanRecord(doc_id="x", level="light", seed=0, dpi=200, pages=[[operation]])


def test_unknown_level_is_rejected():
    with pytest.raises(ValidationError):
        ScanRecord(doc_id="x", level="extreme", seed=0, dpi=200, pages=[])


def test_an_operation_without_apply_cannot_be_created():
    class Incomplete(_Operation):
        pass

    with pytest.raises(TypeError, match="abstract"):
        Incomplete()
