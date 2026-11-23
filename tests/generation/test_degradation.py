"""Image degradations that make a rendered page look scanned."""

import numpy as np
import pytest

from actadoc.generation._degradation import (
    add_noise,
    blur,
    fold,
    jpeg_compress,
    rotate,
    stamp,
    uneven_lighting,
)


@pytest.fixture
def page():
    """White page with a black rectangle, like a line of text."""
    image = np.full((200, 150), 255, dtype=np.uint8)
    image[90:110, 30:120] = 0
    return image


@pytest.fixture
def rng():
    return np.random.default_rng(0)


def test_rotation_keeps_shape_and_fills_corners_with_white(page):
    rotated = rotate(page, 10)
    assert rotated.shape == page.shape and rotated.dtype == np.uint8
    assert rotated[0, 0] == 255
    assert not np.array_equal(rotated, page)


def test_zero_rotation_is_identity(page):
    assert np.array_equal(rotate(page, 0), page)


def test_noise_has_the_requested_strength(rng):
    gray = np.full((200, 200), 128, dtype=np.uint8)  # mid-gray: no clipping
    deviation = np.abs(add_noise(gray, 10, rng).astype(int) - 128).mean()
    assert deviation == pytest.approx(10 * np.sqrt(2 / np.pi), rel=0.05)  # mean |N(0, sigma)|


def test_noise_stays_within_gray_levels(page, rng):
    noisy = add_noise(page, 50, rng)
    assert noisy.dtype == np.uint8 and noisy.min() == 0 and noisy.max() == 255


def test_noise_is_reproducible_with_the_same_seed(page):
    first = add_noise(page, 10, np.random.default_rng(1))
    second = add_noise(page, 10, np.random.default_rng(1))
    assert np.array_equal(first, second)


def test_zero_noise_is_identity(page, rng):
    assert np.array_equal(add_noise(page, 0, rng), page)


def test_blur_softens_edges(page):
    blurred = blur(page, 7)
    assert 0 < blurred[89, 60] < 255  # just above the rectangle, now gray
    assert np.array_equal(blur(page, 1), page)


@pytest.mark.parametrize("kernel", [0, 2, -3])
def test_invalid_blur_kernel_is_rejected(page, kernel):
    with pytest.raises(ValueError, match="kernel"):
        blur(page, kernel)


def test_lower_jpeg_quality_loses_more(page, rng):
    noisy = add_noise(page, 20, rng)
    error = {q: np.abs(jpeg_compress(noisy, q).astype(int) - noisy).mean() for q in (95, 20)}
    assert error[20] > error[95]


@pytest.mark.parametrize("quality", [0, 101])
def test_invalid_jpeg_quality_is_rejected(page, quality):
    with pytest.raises(ValueError, match="quality"):
        jpeg_compress(page, quality)


def test_lighting_darkens_one_edge_only(page):
    lit = uneven_lighting(page, 0.4, direction=0)
    assert lit[0, 0] == 255  # left edge untouched
    assert lit[0, -1] == pytest.approx(255 * 0.6, abs=1)  # right edge darkened by 40 %


def test_zero_lighting_is_identity(page):
    assert np.array_equal(uneven_lighting(page, 0, direction=45), page)


@pytest.mark.parametrize("strength", [-0.1, 1.5])
def test_invalid_lighting_strength_is_rejected(page, strength):
    with pytest.raises(ValueError, match="strength"):
        uneven_lighting(page, strength, direction=0)


def test_negative_noise_is_rejected(page, rng):
    with pytest.raises(ValueError, match="sigma"):
        add_noise(page, -1, rng)


@pytest.mark.parametrize(
    "image", [np.zeros((4, 4, 3), dtype=np.uint8), np.zeros((4, 4), dtype=np.float32)]
)
def test_non_grayscale_uint8_image_is_rejected(image):
    with pytest.raises(ValueError, match="2-D uint8"):
        rotate(image, 1)


def test_stamp_adds_ink_around_its_centre(page):
    stamped = stamp(page, centre=(75, 50), radius=30, text="COPIE", intensity=0.7)
    assert stamped.shape == page.shape and stamped.dtype == np.uint8
    assert stamped[50, 45] < 255  # on the outer ring (75 - 30, 50)
    assert stamped[190, 140] == 255  # far from the stamp


def test_stamp_is_blended_not_opaque(page):
    stamped = stamp(page, centre=(75, 100), radius=40, text="COPIE", intensity=0.5)
    assert stamped.min() >= 0 and (stamped[(stamped > 0) & (stamped < 255)] >= 127).all()


def test_zero_intensity_stamp_is_identity(page):
    assert np.array_equal(stamp(page, (75, 100), 30, "COPIE", 0), page)


@pytest.mark.parametrize(
    ("radius", "text", "intensity", "match"),
    [(0, "COPIE", 0.5, "radius"), (30, "ENREGISTRÉ", 0.5, "ASCII"), (30, "COPIE", 2, "intensity")],
)
def test_invalid_stamp_is_rejected(page, radius, text, intensity, match):
    with pytest.raises(ValueError, match=match):
        stamp(page, (75, 100), radius, text, intensity)


def test_fold_darkens_a_horizontal_band(page):
    folded = fold(page, position=1 / 3, darkness=0.3, width=5)
    row = round((page.shape[0] - 1) / 3)
    assert folded[row, 0] == pytest.approx(255 * 0.7, abs=1)
    assert folded[0, 0] == 255 and folded[-1, 0] == 255


def test_zero_darkness_fold_is_identity(page):
    assert np.array_equal(fold(page, 0.5, 0, 5), page)


@pytest.mark.parametrize(
    ("position", "darkness", "width", "match"),
    [(1.2, 0.3, 5, "position"), (0.5, -0.1, 5, "darkness"), (0.5, 0.3, 0, "width")],
)
def test_invalid_fold_is_rejected(page, position, darkness, width, match):
    with pytest.raises(ValueError, match=match):
        fold(page, position, darkness, width)
