"""Image degradations that make a rendered page look scanned.

Every operation is a pure function: it takes a grayscale page (``uint8``
array, white is 255) and returns a new page of the same shape and type. Random
choices come from an explicit :class:`numpy.random.Generator`.
"""

from __future__ import annotations

import cv2
import numpy as np
from numpy.typing import NDArray

Image = NDArray[np.uint8]

WHITE = 255


def _check(image: Image) -> None:
    """Reject anything that is not a grayscale ``uint8`` page."""
    if image.ndim != 2 or image.dtype != np.uint8:
        raise ValueError(f"expected a 2-D uint8 image, got {image.ndim}-D {image.dtype}")


def rotate(image: Image, angle: float) -> Image:
    """Rotate a page around its centre, filling the corners with white.

    Parameters
    ----------
    image : numpy.ndarray
        Grayscale page, ``uint8``.
    angle : float
        Angle in degrees, counter-clockwise.

    Returns
    -------
    numpy.ndarray
        Rotated page, same shape.

    Raises
    ------
    ValueError
        If ``image`` is not a 2-D ``uint8`` array.
    """
    _check(image)
    height, width = image.shape
    matrix = cv2.getRotationMatrix2D((width / 2, height / 2), angle, 1.0)
    rotated = cv2.warpAffine(
        image, matrix, (width, height), flags=cv2.INTER_LINEAR, borderValue=WHITE
    )
    return np.asarray(rotated, dtype=np.uint8)


def add_noise(image: Image, sigma: float, rng: np.random.Generator) -> Image:
    """Add Gaussian sensor noise.

    Parameters
    ----------
    image : numpy.ndarray
        Grayscale page, ``uint8``.
    sigma : float
        Standard deviation of the noise, in gray levels, ``>= 0``.
    rng : numpy.random.Generator
        Source of randomness.

    Returns
    -------
    numpy.ndarray
        Noisy page, values clipped to 0-255.

    Raises
    ------
    ValueError
        If ``image`` is not a 2-D ``uint8`` array or ``sigma`` is negative.
    """
    _check(image)
    if sigma < 0:
        raise ValueError(f"sigma must be non-negative, got {sigma}")
    noise = rng.normal(0.0, sigma, image.shape)
    return np.clip(image + noise, 0, WHITE).astype(np.uint8)


def blur(image: Image, kernel: int) -> Image:
    """Blur a page, as an out-of-focus scanner does.

    Parameters
    ----------
    image : numpy.ndarray
        Grayscale page, ``uint8``.
    kernel : int
        Size of the Gaussian kernel, odd and ``>= 1``; ``1`` leaves the page unchanged.

    Returns
    -------
    numpy.ndarray
        Blurred page.

    Raises
    ------
    ValueError
        If ``image`` is not a 2-D ``uint8`` array or ``kernel`` is not a positive odd number.
    """
    _check(image)
    if kernel < 1 or kernel % 2 == 0:
        raise ValueError(f"kernel must be a positive odd number, got {kernel}")
    return np.asarray(cv2.GaussianBlur(image, (kernel, kernel), 0), dtype=np.uint8)


def jpeg_compress(image: Image, quality: int) -> Image:
    """Compress a page to JPEG and decode it back, keeping the artefacts.

    Parameters
    ----------
    image : numpy.ndarray
        Grayscale page, ``uint8``.
    quality : int
        JPEG quality, from 1 (worst) to 100 (best).

    Returns
    -------
    numpy.ndarray
        Page with compression artefacts.

    Raises
    ------
    ValueError
        If ``image`` is not a 2-D ``uint8`` array or ``quality`` is outside 1-100.
    """
    _check(image)
    if not 1 <= quality <= 100:
        raise ValueError(f"quality must be between 1 and 100, got {quality}")
    _, encoded = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return np.asarray(cv2.imdecode(encoded, cv2.IMREAD_GRAYSCALE), dtype=np.uint8)


def uneven_lighting(image: Image, strength: float, direction: float) -> Image:
    """Darken a page progressively, as a lid not fully closed does.

    Parameters
    ----------
    image : numpy.ndarray
        Grayscale page, ``uint8``.
    strength : float
        Darkening of the darkest edge, from 0 (none) to 1 (black).
    direction : float
        Direction of the gradient in degrees; ``0`` darkens the right edge.

    Returns
    -------
    numpy.ndarray
        Page with a lighting gradient.

    Raises
    ------
    ValueError
        If ``image`` is not a 2-D ``uint8`` array or ``strength`` is outside 0-1.
    """
    _check(image)
    if not 0 <= strength <= 1:
        raise ValueError(f"strength must be between 0 and 1, got {strength}")
    height, width = image.shape
    rows, cols = np.mgrid[0:height, 0:width]
    radians = np.deg2rad(direction)
    position = cols * np.cos(radians) + rows * np.sin(radians)
    position = (position - position.min()) / max(float(np.ptp(position)), 1.0)
    factor = 1.0 - strength * position
    return np.clip(image * factor, 0, WHITE).astype(np.uint8)
