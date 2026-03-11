"""Tests for brand-profile.json schema, validation, and file writing.

Covers all required top-level fields, nested structure, Pydantic validation
errors for invalid data, and the file-write helper.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from daf.cli.brand_profile import (
    BrandProfile,
    ColorsConfig,
    TypographyConfig,
    SpacingConfig,
    ThemesConfig,
    MotionConfig,
    AccessibilityConfig,
    from_interview_result,
    write_brand_profile,
)
from daf.cli.interview import InterviewResult


# ---------------------------------------------------------------------------
# Field presence & types
# ---------------------------------------------------------------------------


def _valid_profile() -> BrandProfile:
    return BrandProfile(
        name="Acme",
        archetype="enterprise-b2b",
        componentScope="comprehensive",
        colors=ColorsConfig(
            primary="#0A2463",
            secondary="#3E92CC",
            neutral="#D8D8D8",
        ),
        typography=TypographyConfig(
            fontFamilyHeading="Inter",
            fontFamilyBody="Inter",
            scale="major-third",
        ),
        spacing=SpacingConfig(base="4px"),
        borderRadius="medium",
        elevation="3-step",
        motion=MotionConfig(duration="200ms", easing="ease-in-out"),
        breakpoints=["sm:640px", "md:768px", "lg:1024px", "xl:1280px"],
        accessibility=AccessibilityConfig(level="AA"),
        themes=ThemesConfig(
            modes=["light", "dark"],
            default="light",
            brands=[],
            brandOverrides={},
        ),
        componentOverrides={},
        iconSet=None,
        plugins=[],
    )


def test_valid_profile_instantiates() -> None:
    p = _valid_profile()
    assert p.name == "Acme"
    assert p.archetype == "enterprise-b2b"


def test_required_fields_present() -> None:
    """BrandProfile has all contractually required top-level fields."""
    p = _valid_profile()
    required = [
        "name", "archetype", "componentScope", "colors", "typography",
        "spacing", "borderRadius", "elevation", "motion", "breakpoints",
        "accessibility", "themes", "componentOverrides", "plugins",
    ]
    for attr in required:
        assert hasattr(p, attr), f"Missing field: {attr}"


def test_invalid_archetype_raises() -> None:
    with pytest.raises(ValidationError):
        BrandProfile(
            name="Acme",
            archetype="unknown-type",  # invalid
            componentScope="starter",
            colors=ColorsConfig(primary="#000", secondary="#111", neutral="#222"),
            typography=TypographyConfig(fontFamilyHeading="Sans", fontFamilyBody="Sans", scale="x"),
            spacing=SpacingConfig(base="4px"),
            borderRadius="none",
            elevation="flat",
            motion=MotionConfig(duration="100ms", easing="linear"),
            breakpoints=[],
            accessibility=AccessibilityConfig(level="AA"),
            themes=ThemesConfig(modes=["light"], default="light", brands=[], brandOverrides={}),
            componentOverrides={},
            iconSet=None,
            plugins=[],
        )


def test_invalid_component_scope_raises() -> None:
    with pytest.raises(ValidationError):
        p = _valid_profile()
        BrandProfile(**{**p.model_dump(), "componentScope": "mega"})


def test_invalid_accessibility_level_raises() -> None:
    p = _valid_profile()
    data = p.model_dump()
    data["accessibility"]["level"] = "A"  # only AA/AAA allowed
    with pytest.raises(ValidationError):
        BrandProfile(**data)


def test_themes_brands_defaults_empty() -> None:
    p = _valid_profile()
    assert p.themes.brands == []
    assert p.themes.brandOverrides == {}


def test_multi_brand_themes() -> None:
    p = _valid_profile()
    data = p.model_dump()
    data["themes"]["brands"] = ["brand-a", "brand-b"]
    data["themes"]["brandOverrides"] = {"brand-a": {"colors": {"primary": "#FF0000"}}}
    p2 = BrandProfile(**data)
    assert p2.themes.brands == ["brand-a", "brand-b"]


# ---------------------------------------------------------------------------
# from_interview_result
# ---------------------------------------------------------------------------


def _make_interview_result() -> InterviewResult:
    return InterviewResult(
        name="Acme Corp",
        archetype="enterprise-b2b",
        primary_color="#0A2463",
        secondary_color="#3E92CC",
        neutral_color="#D8D8D8",
        font_family_heading="Inter",
        font_family_body="Inter",
        font_scale="major-third",
        spacing_scale="4px",
        component_scope="comprehensive",
        border_radius="medium",
        elevation_scale="3-step",
        motion_duration="200ms",
        motion_easing="ease-in-out",
        breakpoints=["sm:640px"],
        accessibility_level="AA",
        theme_modes=["light", "dark"],
        theme_default="light",
        multi_brand_names=[],
    )


def test_from_interview_result_produces_valid_profile() -> None:
    result = from_interview_result(_make_interview_result())
    assert isinstance(result, BrandProfile)
    assert result.name == "Acme Corp"
    assert result.colors.primary == "#0A2463"
    assert result.themes.modes == ["light", "dark"]


def test_from_interview_result_multi_brand() -> None:
    ir = _make_interview_result()
    ir.multi_brand_names = ["brand-a", "brand-b"]
    profile = from_interview_result(ir)
    assert profile.themes.brands == ["brand-a", "brand-b"]


# ---------------------------------------------------------------------------
# write_brand_profile
# ---------------------------------------------------------------------------


def test_write_brand_profile_creates_file(tmp_path: Path) -> None:
    profile = _valid_profile()
    out = tmp_path / "brand-profile.json"
    write_brand_profile(profile, tmp_path)
    assert out.exists()
    data = json.loads(out.read_text())
    assert data["name"] == "Acme"


def test_write_brand_profile_valid_json(tmp_path: Path) -> None:
    profile = _valid_profile()
    write_brand_profile(profile, tmp_path)
    out = tmp_path / "brand-profile.json"
    # Must be valid JSON and round-trip cleanly
    loaded = json.loads(out.read_text())
    assert loaded["archetype"] == "enterprise-b2b"


def test_write_brand_profile_overwrites_existing(tmp_path: Path) -> None:
    profile = _valid_profile()
    write_brand_profile(profile, tmp_path)
    profile2 = _valid_profile()
    profile2 = BrandProfile(**{**profile2.model_dump(), "name": "Updated"})
    write_brand_profile(profile2, tmp_path)
    data = json.loads((tmp_path / "brand-profile.json").read_text())
    assert data["name"] == "Updated"
