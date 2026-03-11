"""Tests for Human Gate — Brand Profile Approval.

Covers:
  - Summary display contains required fields
  - Approve choice proceeds
  - Re-run interview choice returns to interview start
  - Provide file choice exits with instructions
  - Hand-written brand-profile.json in output folder bypasses interview
  - Invalid schema in hand-written file is rejected fast
"""

from __future__ import annotations

import json
from pathlib import Path

from daf.cli.brand_profile import BrandProfile, ColorsConfig, TypographyConfig
from daf.cli.brand_profile import SpacingConfig, ThemesConfig, MotionConfig, AccessibilityConfig
from daf.cli.human_gate import BrandProfileGate, GateChoice


def _valid_profile() -> BrandProfile:
    return BrandProfile(
        name="Acme",
        archetype="enterprise-b2b",
        componentScope="comprehensive",
        colors=ColorsConfig(primary="#0A2463", secondary="#3E92CC", neutral="#D8D8D8"),
        typography=TypographyConfig(fontFamilyHeading="Inter", fontFamilyBody="Inter", scale="major-third"),
        spacing=SpacingConfig(base="4px"),
        borderRadius="medium",
        elevation="3-step",
        motion=MotionConfig(duration="200ms", easing="ease-in-out"),
        breakpoints=["sm:640px"],
        accessibility=AccessibilityConfig(level="AA"),
        themes=ThemesConfig(modes=["light", "dark"], default="light", brands=[], brandOverrides={}),
        componentOverrides={},
        iconSet=None,
        plugins=[],
    )


def test_summary_contains_brand_name() -> None:
    gate = BrandProfileGate(profile=_valid_profile(), input_lines=["1"])
    summary = gate.build_summary()
    assert "Acme" in summary


def test_summary_contains_archetype() -> None:
    gate = BrandProfileGate(profile=_valid_profile(), input_lines=["1"])
    summary = gate.build_summary()
    assert "enterprise-b2b" in summary


def test_summary_contains_component_scope() -> None:
    gate = BrandProfileGate(profile=_valid_profile(), input_lines=["1"])
    summary = gate.build_summary()
    assert "comprehensive" in summary


def test_summary_contains_primary_color() -> None:
    gate = BrandProfileGate(profile=_valid_profile(), input_lines=["1"])
    summary = gate.build_summary()
    assert "#0A2463" in summary


def test_summary_contains_accessibility_level() -> None:
    gate = BrandProfileGate(profile=_valid_profile(), input_lines=["1"])
    summary = gate.build_summary()
    assert "AA" in summary


def test_approve_returns_approve() -> None:
    """Choosing '1' → Approve returns GateChoice.APPROVE."""
    gate = BrandProfileGate(profile=_valid_profile(), input_lines=["1"])
    choice = gate.run()
    assert choice == GateChoice.APPROVE


def test_rerun_returns_rerun() -> None:
    """Choosing '2' → Re-run interview returns GateChoice.RERUN."""
    gate = BrandProfileGate(profile=_valid_profile(), input_lines=["2"])
    choice = gate.run()
    assert choice == GateChoice.RERUN


def test_provide_file_returns_provide_file() -> None:
    """Choosing '3' → Provide file returns GateChoice.PROVIDE_FILE."""
    gate = BrandProfileGate(profile=_valid_profile(), input_lines=["3"])
    choice = gate.run()
    assert choice == GateChoice.PROVIDE_FILE


def test_invalid_choice_reprompts() -> None:
    """Invalid input is re-prompted; valid choice is eventually accepted."""
    gate = BrandProfileGate(profile=_valid_profile(), input_lines=["x", "99", "1"])
    choice = gate.run()
    assert choice == GateChoice.APPROVE


def test_load_from_file_valid(tmp_path: Path) -> None:
    """BrandProfileGate.load_from_file returns a BrandProfile for valid JSON."""
    profile = _valid_profile()
    f = tmp_path / "brand-profile.json"
    f.write_text(json.dumps(profile.model_dump(mode="json")))
    loaded = BrandProfileGate.load_from_file(f)
    assert loaded.name == "Acme"


def test_load_from_file_missing_raises(tmp_path: Path) -> None:
    """load_from_file raises FileNotFoundError for missing file."""
    import pytest
    with pytest.raises(FileNotFoundError):
        BrandProfileGate.load_from_file(tmp_path / "missing.json")


def test_load_from_file_invalid_schema_raises(tmp_path: Path) -> None:
    """load_from_file raises ValidationError for invalid schema content."""
    from pydantic import ValidationError
    import pytest
    f = tmp_path / "brand-profile.json"
    f.write_text(json.dumps({"name": "X", "archetype": "bad-type"}))  # invalid archetype
    with pytest.raises(ValidationError):
        BrandProfileGate.load_from_file(f)
