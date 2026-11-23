"""Scan simulation: degradation levels, operation records, and their application."""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated, Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from actadoc.generation._degradation import (
    Image,
    add_noise,
    blur,
    fold,
    jpeg_compress,
    rotate,
    stamp,
    uneven_lighting,
)

SCAN_SCHEMA_VERSION = "1.0"

_STAMP_WORDS = ("COPIE", "ARCHIVES", "RECU", "ENREGISTRE")


class ScanLevel(StrEnum):
    """How strongly a rendered document is degraded."""

    CLEAN = "clean"
    LIGHT = "light"
    MEDIUM = "medium"
    HEAVY = "heavy"


@dataclass(frozen=True)
class ScanProfile:
    """Parameter ranges of one degradation level.

    Parameters
    ----------
    max_rotation : float
        Largest rotation in degrees, either direction.
    noise_sigma : tuple of float
        Range of the Gaussian noise standard deviation, in gray levels.
    blur_kernels : tuple of int
        Kernel sizes to choose from; ``1`` means no blur.
    jpeg_quality : tuple of int or None
        Range of JPEG quality, or ``None`` for no compression.
    max_lighting : float
        Largest darkening of the lighting gradient, from 0 to 1.
    stamp_probability : float
        Probability that a page gets a stamp.
    fold_probability : float
        Probability that a page gets a fold.
    """

    max_rotation: float
    noise_sigma: tuple[float, float]
    blur_kernels: tuple[int, ...]
    jpeg_quality: tuple[int, int] | None
    max_lighting: float
    stamp_probability: float
    fold_probability: float


PROFILES: dict[ScanLevel, ScanProfile] = {
    ScanLevel.CLEAN: ScanProfile(0.0, (0.0, 0.0), (1,), None, 0.0, 0.0, 0.0),
    ScanLevel.LIGHT: ScanProfile(0.5, (2.0, 5.0), (1,), (80, 95), 0.10, 0.0, 0.0),
    ScanLevel.MEDIUM: ScanProfile(1.5, (5.0, 10.0), (1, 3), (55, 80), 0.25, 0.5, 0.5),
    ScanLevel.HEAVY: ScanProfile(3.0, (10.0, 18.0), (3, 5), (30, 55), 0.40, 1.0, 1.0),
}


class _Operation(BaseModel):
    """Base of the recorded operations: immutable, unknown fields rejected."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    @abstractmethod
    def apply(self, image: Image) -> Image:
        """Apply this operation to a page."""


class Rotate(_Operation):
    """Rotation by ``angle`` degrees, see :func:`rotate`."""

    name: Literal["rotate"] = "rotate"
    angle: float

    def apply(self, image: Image) -> Image:
        """Apply this operation to a page."""
        return rotate(image, self.angle)


class Fold(_Operation):
    """Fold shadow, see :func:`fold`."""

    name: Literal["fold"] = "fold"
    position: float = Field(ge=0, le=1)
    darkness: float = Field(ge=0, le=1)
    width: int = Field(ge=1)

    def apply(self, image: Image) -> Image:
        """Apply this operation to a page."""
        return fold(image, self.position, self.darkness, self.width)


class Stamp(_Operation):
    """Ink stamp, see :func:`stamp`."""

    name: Literal["stamp"] = "stamp"
    centre: tuple[int, int]
    radius: int = Field(ge=1)
    text: str
    intensity: float = Field(ge=0, le=1)

    def apply(self, image: Image) -> Image:
        """Apply this operation to a page."""
        return stamp(image, self.centre, self.radius, self.text, self.intensity)


class Lighting(_Operation):
    """Lighting gradient, see :func:`uneven_lighting`."""

    name: Literal["lighting"] = "lighting"
    strength: float = Field(ge=0, le=1)
    direction: float

    def apply(self, image: Image) -> Image:
        """Apply this operation to a page."""
        return uneven_lighting(image, self.strength, self.direction)


class Blur(_Operation):
    """Gaussian blur, see :func:`blur`."""

    name: Literal["blur"] = "blur"
    kernel: int = Field(ge=1)

    def apply(self, image: Image) -> Image:
        """Apply this operation to a page."""
        return blur(image, self.kernel)


class Noise(_Operation):
    """Gaussian noise, see :func:`add_noise`; ``seed`` makes it replayable."""

    name: Literal["noise"] = "noise"
    sigma: float = Field(ge=0)
    seed: int = Field(ge=0)

    def apply(self, image: Image) -> Image:
        """Apply this operation to a page."""
        return add_noise(image, self.sigma, np.random.default_rng(self.seed))


class Jpeg(_Operation):
    """JPEG compression, see :func:`jpeg_compress`."""

    name: Literal["jpeg"] = "jpeg"
    quality: int = Field(ge=1, le=100)

    def apply(self, image: Image) -> Image:
        """Apply this operation to a page."""
        return jpeg_compress(image, self.quality)


# The ``name`` field tells Pydantic which model to read a JSON operation into.
Operation = Annotated[
    Rotate | Fold | Stamp | Lighting | Blur | Noise | Jpeg, Field(discriminator="name")
]


class ScanRecord(BaseModel):
    """What was done to turn a rendered document into a scanned one.

    Parameters
    ----------
    doc_id : str
        Identifier of the document.
    level : ScanLevel
        Degradation level.
    seed : int
        Seed the operations were drawn from.
    dpi : int
        Resolution of the scanned pages.
    pages : list of list of Operation
        Operations applied to each page, in order. Each operation is one of
        :class:`Rotate`, :class:`Fold`, :class:`Stamp`, :class:`Lighting`,
        :class:`Blur`, :class:`Noise`, :class:`Jpeg`, told apart by ``name``.
    container_quality : int, default=95
        JPEG quality of the pages inside the scanned PDF, as set on a scanner.
        Even the ``clean`` level goes through this compression.
    schema_version : str, default=SCAN_SCHEMA_VERSION
        Version of this record format.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    doc_id: str
    level: ScanLevel
    seed: int
    dpi: int
    pages: list[list[Operation]]
    container_quality: int = Field(default=95, ge=1, le=100)
    schema_version: str = SCAN_SCHEMA_VERSION


def sample_operations(
    profile: ScanProfile, shape: tuple[int, int], rng: np.random.Generator
) -> list[Operation]:
    """Draw the degradations of one page from a profile.

    Operations that would leave the page unchanged are left out, so a clean
    profile gives an empty list.

    Parameters
    ----------
    profile : ScanProfile
        Parameter ranges.
    shape : tuple of int
        Page shape, ``(height, width)`` in pixels.
    rng : numpy.random.Generator
        Source of randomness.

    Returns
    -------
    list of Operation
        Operations in the order they must be applied: geometry first, then
        marks on the paper, then optics, then sensor noise and compression.
    """
    height, width = shape
    operations: list[Operation] = []
    if profile.max_rotation > 0:
        angle = round(float(rng.uniform(-profile.max_rotation, profile.max_rotation)), 3)
        operations.append(Rotate(angle=angle))
    if rng.random() < profile.fold_probability:
        operations.append(
            Fold(
                position=round(float(rng.choice([1 / 3, 1 / 2, 2 / 3])), 4),
                darkness=round(float(rng.uniform(0.1, 0.3)), 3),
                width=int(rng.integers(3, 12)),
            )
        )
    if rng.random() < profile.stamp_probability:
        radius = int(rng.integers(width // 14, width // 9))
        centre = (
            int(rng.integers(radius, width - radius)),
            int(rng.integers(radius, height - radius)),
        )
        operations.append(
            Stamp(
                centre=centre,
                radius=radius,
                text=str(rng.choice(_STAMP_WORDS)),
                intensity=round(float(rng.uniform(0.3, 0.6)), 3),
            )
        )
    if profile.max_lighting > 0:
        operations.append(
            Lighting(
                strength=round(float(rng.uniform(0, profile.max_lighting)), 3),
                direction=round(float(rng.uniform(0, 360)), 1),
            )
        )
    kernel = int(rng.choice(profile.blur_kernels))
    if kernel > 1:
        operations.append(Blur(kernel=kernel))
    if profile.noise_sigma[1] > 0:
        operations.append(
            Noise(
                sigma=round(float(rng.uniform(*profile.noise_sigma)), 2),
                seed=int(rng.integers(2**32)),
            )
        )
    if profile.jpeg_quality is not None:
        low, high = profile.jpeg_quality
        quality = int(rng.integers(low, high + 1))
        operations.append(Jpeg(quality=quality))
    return operations


def apply_operations(image: Image, operations: list[Operation]) -> Image:
    """Apply recorded degradations to a page, in order.

    Parameters
    ----------
    image : numpy.ndarray
        Grayscale page, ``uint8``.
    operations : list of Operation
        Operations from :func:`sample_operations` or from a :class:`ScanRecord`.

    Returns
    -------
    numpy.ndarray
        Degraded page. The same operations always give the same page.
    """
    for operation in operations:
        image = operation.apply(image)
    return image
