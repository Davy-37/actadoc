"""Package metadata."""

import re

import actadoc

SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


def test_version_is_semantic():
    assert SEMVER.match(actadoc.__version__)


def test_version_matches_installed_metadata():
    from importlib.metadata import version

    assert version("actadoc") == actadoc.__version__
