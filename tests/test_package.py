"""Task 1.1 — verify the Python package layout is importable and correctly structured."""

import importlib


def test_daf_package_importable() -> None:
    mod = importlib.import_module("daf")
    assert mod is not None


def test_subpackages_importable() -> None:
    for sub in ("daf.config", "daf.plugins", "daf.output", "daf.cli"):
        mod = importlib.import_module(sub)
        assert mod is not None
