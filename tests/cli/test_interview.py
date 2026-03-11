"""Tests for brand interview conversation flow.

Covers every required field, re-prompting on invalid input, and
multi-brand configuration. Uses simulated stdin via Click's CliRunner.
"""

from __future__ import annotations

from daf.cli.interview import BrandInterviewer, InterviewResult


# ---------------------------------------------------------------------------
# Unit tests for BrandInterviewer (field-by-field)
# ---------------------------------------------------------------------------


def test_interview_result_has_all_required_fields() -> None:
    """InterviewResult exposes all required brand-profile top-level fields."""
    result = InterviewResult(
        name="Acme",
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
        breakpoints=["sm:640px", "md:768px", "lg:1024px", "xl:1280px"],
        accessibility_level="AA",
        theme_modes=["light", "dark"],
        theme_default="light",
        multi_brand_names=[],
    )
    assert result.name == "Acme"
    assert result.archetype == "enterprise-b2b"
    assert result.accessibility_level == "AA"


def test_valid_archetypes() -> None:
    """BrandInterviewer accepts all five valid archetype values."""
    from daf.cli.interview import VALID_ARCHETYPES

    assert VALID_ARCHETYPES == {
        "enterprise-b2b",
        "consumer-b2c",
        "mobile-first",
        "multi-brand-platform",
        "custom",
    }


def test_valid_hex_color_accepted() -> None:
    """BrandInterviewer.parse_color accepts standard hex values."""
    from daf.cli.interview import parse_color

    assert parse_color("#0A2463") == "#0A2463"
    assert parse_color("#fff") == "#fff"


def test_invalid_color_raises() -> None:
    """BrandInterviewer.parse_color raises ValueError for unparseable input."""
    from daf.cli.interview import parse_color
    import pytest

    with pytest.raises(ValueError, match="color"):
        parse_color("not-a-color")


def test_valid_rgb_color_accepted() -> None:
    """parse_color accepts rgb(...) notation."""
    from daf.cli.interview import parse_color

    assert parse_color("rgb(10, 36, 99)") == "rgb(10, 36, 99)"


def test_valid_hsl_color_accepted() -> None:
    """parse_color accepts hsl(...) notation."""
    from daf.cli.interview import parse_color

    assert parse_color("hsl(225, 80%, 21%)") == "hsl(225, 80%, 21%)"


def test_valid_component_scopes() -> None:
    """BrandInterviewer only accepts starter/standard/comprehensive."""
    from daf.cli.interview import VALID_COMPONENT_SCOPES

    assert VALID_COMPONENT_SCOPES == {"starter", "standard", "comprehensive"}


def test_valid_accessibility_levels() -> None:
    """BrandInterviewer only accepts AA/AAA."""
    from daf.cli.interview import VALID_ACCESSIBILITY_LEVELS

    assert VALID_ACCESSIBILITY_LEVELS == {"AA", "AAA"}


def test_interviewer_run_produces_result(monkeypatch: object) -> None:
    """BrandInterviewer.run() returns an InterviewResult when given valid answers."""
    answers = [
        "Acme Corp",           # brand name
        "enterprise-b2b",      # archetype
        "#0A2463",             # primary color
        "#3E92CC",             # secondary color
        "#D8D8D8",             # neutral color
        "Inter",               # font heading
        "Inter",               # font body
        "major-third",         # font scale
        "4px",                 # spacing scale
        "comprehensive",       # component scope
        "medium",              # border radius
        "3-step",              # elevation scale
        "200ms",               # motion duration
        "ease-in-out",         # motion easing
        "sm:640px,md:768px",   # breakpoints
        "AA",                  # accessibility level
        "light,dark",          # theme modes
        "light",               # default theme
        "no",                  # multi-brand?
    ]
    interviewer = BrandInterviewer(input_lines=answers)
    result = interviewer.run()
    assert isinstance(result, InterviewResult)
    assert result.name == "Acme Corp"
    assert result.archetype == "enterprise-b2b"
    assert result.primary_color == "#0A2463"
    assert result.component_scope == "comprehensive"
    assert result.accessibility_level == "AA"
    assert result.multi_brand_names == []


def test_interviewer_re_prompts_invalid_color(monkeypatch: object) -> None:
    """BrandInterviewer re-prompts when an invalid color is entered initially."""
    answers = [
        "Acme Corp",
        "enterprise-b2b",
        "not-a-color",    # invalid — should re-prompt
        "#0A2463",        # valid on retry
        "#3E92CC",
        "#D8D8D8",
        "Inter",
        "Inter",
        "major-third",
        "4px",
        "comprehensive",
        "medium",
        "3-step",
        "200ms",
        "ease-in-out",
        "sm:640px",
        "AA",
        "light",
        "light",
        "no",
    ]
    interviewer = BrandInterviewer(input_lines=answers)
    result = interviewer.run()
    assert result.primary_color == "#0A2463"


def test_interviewer_multi_brand(monkeypatch: object) -> None:
    """BrandInterviewer collects per-brand identifiers when multi-brand is yes."""
    answers = [
        "GlobalCo",
        "multi-brand-platform",
        "#111111",
        "#222222",
        "#333333",
        "Roboto",
        "Roboto",
        "major-third",
        "4px",
        "standard",
        "small",
        "3-step",
        "150ms",
        "ease-out",
        "sm:640px",
        "AA",
        "light,dark",
        "light",
        "yes",           # multi-brand
        "brand-a",       # first brand id
        "brand-b",       # second brand id
        "",              # done entering brands
    ]
    interviewer = BrandInterviewer(input_lines=answers)
    result = interviewer.run()
    assert result.multi_brand_names == ["brand-a", "brand-b"]
