"""Brand profile schema, validation, and file I/O.

Defines the full ``BrandProfile`` Pydantic model corresponding to the
``brand-profile.json`` contract.  Provides:

* ``BrandProfile`` — the top-level validated model.
* ``from_interview_result()`` — convert a ``BrandInterviewer`` result to a profile.
* ``write_brand_profile()`` — serialise and write to ``<output>/brand-profile.json``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Optional

from pydantic import BaseModel, field_validator

if TYPE_CHECKING:
    from daf.cli.interview import InterviewResult


# ---------------------------------------------------------------------------
# Nested config models
# ---------------------------------------------------------------------------


class ColorsConfig(BaseModel):
    primary: str
    secondary: str
    neutral: str


class TypographyConfig(BaseModel):
    fontFamilyHeading: str
    fontFamilyBody: str
    scale: str


class SpacingConfig(BaseModel):
    base: str


class MotionConfig(BaseModel):
    duration: str
    easing: str


class AccessibilityConfig(BaseModel):
    level: Literal["AA", "AAA"]


class ThemesConfig(BaseModel):
    modes: list[str]
    default: str
    brands: list[str] = []
    brandOverrides: dict[str, Any] = {}


# ---------------------------------------------------------------------------
# Top-level brand profile
# ---------------------------------------------------------------------------

_VALID_ARCHETYPES = frozenset(
    {"enterprise-b2b", "consumer-b2c", "mobile-first", "multi-brand-platform", "custom"}
)
_VALID_SCOPES = frozenset({"starter", "standard", "comprehensive"})


class BrandProfile(BaseModel):
    """Full brand-profile.json contract.

    Every field maps 1-to-1 to the JSON keys agreed in the spec.
    """

    name: str
    archetype: str
    componentScope: str
    colors: ColorsConfig
    typography: TypographyConfig
    spacing: SpacingConfig
    borderRadius: str
    elevation: str
    motion: MotionConfig
    breakpoints: list[str]
    accessibility: AccessibilityConfig
    themes: ThemesConfig
    componentOverrides: dict[str, Any] = {}
    iconSet: Optional[str] = None
    plugins: list[str] = []

    @field_validator("archetype")
    @classmethod
    def _validate_archetype(cls, v: str) -> str:
        if v not in _VALID_ARCHETYPES:
            raise ValueError(
                f"archetype must be one of {sorted(_VALID_ARCHETYPES)}, got '{v}'."
            )
        return v

    @field_validator("componentScope")
    @classmethod
    def _validate_scope(cls, v: str) -> str:
        if v not in _VALID_SCOPES:
            raise ValueError(
                f"componentScope must be one of {sorted(_VALID_SCOPES)}, got '{v}'."
            )
        return v


# ---------------------------------------------------------------------------
# Conversion helper
# ---------------------------------------------------------------------------


def from_interview_result(result: "InterviewResult") -> BrandProfile:
    """Convert a completed ``InterviewResult`` to a validated ``BrandProfile``."""
    from daf.cli.interview import InterviewResult as _IR  # noqa: PLC0415

    assert isinstance(result, _IR)

    return BrandProfile(
        name=result.name,
        archetype=result.archetype,
        componentScope=result.component_scope,
        colors=ColorsConfig(
            primary=result.primary_color,
            secondary=result.secondary_color,
            neutral=result.neutral_color,
        ),
        typography=TypographyConfig(
            fontFamilyHeading=result.font_family_heading,
            fontFamilyBody=result.font_family_body,
            scale=result.font_scale,
        ),
        spacing=SpacingConfig(base=result.spacing_scale),
        borderRadius=result.border_radius,
        elevation=result.elevation_scale,
        motion=MotionConfig(
            duration=result.motion_duration,
            easing=result.motion_easing,
        ),
        breakpoints=result.breakpoints,
        accessibility=AccessibilityConfig(level=result.accessibility_level),  # type: ignore[arg-type]
        themes=ThemesConfig(
            modes=result.theme_modes,
            default=result.theme_default,
            brands=result.multi_brand_names,
            brandOverrides={},
        ),
        componentOverrides={},
        iconSet=None,
        plugins=[],
    )


# ---------------------------------------------------------------------------
# File I/O
# ---------------------------------------------------------------------------


def write_brand_profile(profile: BrandProfile, output_dir: Path) -> Path:
    """Serialise *profile* and write it to ``<output_dir>/brand-profile.json``.

    Creates *output_dir* if it does not exist.  Overwrites any existing file.

    Returns
    -------
    Path
        The path of the written file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    dest = output_dir / "brand-profile.json"
    dest.write_text(
        json.dumps(profile.model_dump(mode="json"), indent=2),
        encoding="utf-8",
    )
    return dest
