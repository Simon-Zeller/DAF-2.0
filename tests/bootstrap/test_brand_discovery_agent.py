"""Tests for Brand Discovery Agent (task 4.1).

Test strategy
-------------
* Helper functions (``apply_archetype_defaults``, ``resolve_color``) are tested
  directly — they are deterministic and require no API key.
* CrewAI tools are tested by invoking their ``.run()`` method.
* The ``make_brand_discovery_agent`` factory is tested with a mocked ``LLM`` so
  no live API key is needed; we verify role, tool registration, and model string.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from daf.bootstrap.brand_discovery_agent import (
    ARCHETYPE_DEFAULTS,
    AmbiguousColorError,
    apply_archetype_defaults,
    apply_archetype_defaults_tool,
    make_brand_discovery_agent,
    resolve_color,
    resolve_color_tool,
)


# ---------------------------------------------------------------------------
# apply_archetype_defaults
# ---------------------------------------------------------------------------


def test_enterprise_b2b_defaults_comprehensive_scope() -> None:
    result = apply_archetype_defaults({"archetype": "enterprise-b2b"})
    assert result["componentScope"] == "comprehensive"


def test_enterprise_b2b_defaults_spacing_unit() -> None:
    result = apply_archetype_defaults({"archetype": "enterprise-b2b"})
    assert result["spacing"]["unit"] == 4


def test_enterprise_b2b_defaults_border_radius() -> None:
    result = apply_archetype_defaults({"archetype": "enterprise-b2b"})
    assert result["borderRadius"]["md"] == "2px"


def test_enterprise_b2b_defaults_accessibility_level() -> None:
    result = apply_archetype_defaults({"archetype": "enterprise-b2b"})
    assert result["accessibility"]["level"] == "AA"


def test_consumer_b2c_defaults_standard_scope() -> None:
    result = apply_archetype_defaults({"archetype": "consumer-b2c"})
    assert result["componentScope"] == "standard"


def test_mobile_first_defaults_starter_scope() -> None:
    result = apply_archetype_defaults({"archetype": "mobile-first"})
    assert result["componentScope"] == "starter"


def test_multi_brand_platform_defaults_standard_scope() -> None:
    result = apply_archetype_defaults({"archetype": "multi-brand-platform"})
    assert result["componentScope"] == "standard"


def test_custom_archetype_applies_no_defaults() -> None:
    profile: dict[str, object] = {"archetype": "custom"}
    result = apply_archetype_defaults(profile)
    assert result == {"archetype": "custom"}


def test_defaults_do_not_overwrite_existing_values() -> None:
    profile: dict[str, object] = {"archetype": "enterprise-b2b", "componentScope": "starter"}
    result = apply_archetype_defaults(profile)
    assert result["componentScope"] == "starter"


def test_archetype_defaults_covers_all_non_custom_archetypes() -> None:
    expected = {"enterprise-b2b", "consumer-b2c", "mobile-first", "multi-brand-platform"}
    assert set(ARCHETYPE_DEFAULTS.keys()) == expected


# ---------------------------------------------------------------------------
# resolve_color
# ---------------------------------------------------------------------------


def test_resolve_color_returns_normalized_hex_for_valid_input() -> None:
    assert resolve_color("#1A2B3C") == "#1a2b3c"


def test_resolve_color_accepts_shorthand_hex() -> None:
    assert resolve_color("#fff") == "#ffffff"


def test_resolve_color_raises_for_ambiguous_input() -> None:
    with pytest.raises(AmbiguousColorError):
        resolve_color("kind of blue")


def test_resolve_color_raises_for_empty_string() -> None:
    with pytest.raises(AmbiguousColorError):
        resolve_color("")


# ---------------------------------------------------------------------------
# CrewAI tools
# ---------------------------------------------------------------------------


def test_apply_archetype_defaults_tool_returns_enriched_json() -> None:
    profile = {"archetype": "mobile-first"}
    result = apply_archetype_defaults_tool.run(json.dumps(profile))
    parsed = json.loads(result)
    assert parsed["componentScope"] == "starter"


def test_resolve_color_tool_returns_hex_for_valid_input() -> None:
    result = resolve_color_tool.run("#abc")
    assert result == "#aabbcc"


def test_resolve_color_tool_returns_error_string_for_invalid_input() -> None:
    result = resolve_color_tool.run("not-a-color")
    assert result.startswith("ERROR:")


# ---------------------------------------------------------------------------
# make_brand_discovery_agent factory (Agent + LLM mocked — no API key needed)
# ---------------------------------------------------------------------------
# crewai.Agent is a Pydantic model that deeply validates the `llm` argument.
# Patching both Agent and LLM lets us verify the factory's call arguments
# without triggering LLM construction or any network requests.


@patch("daf.bootstrap.brand_discovery_agent.Agent")
@patch("daf.bootstrap.brand_discovery_agent.LLM")
def test_agent_has_correct_role(mock_llm: MagicMock, mock_agent: MagicMock) -> None:
    make_brand_discovery_agent("claude-sonnet-4-20250514")
    _, kwargs = mock_agent.call_args
    assert kwargs["role"] == "Brand Profile Validator and Enricher"


@patch("daf.bootstrap.brand_discovery_agent.Agent")
@patch("daf.bootstrap.brand_discovery_agent.LLM")
def test_agent_llm_constructed_with_anthropic_prefix(mock_llm: MagicMock, mock_agent: MagicMock) -> None:
    make_brand_discovery_agent("claude-sonnet-4-20250514")
    mock_llm.assert_called_once_with(model="anthropic/claude-sonnet-4-20250514")


@patch("daf.bootstrap.brand_discovery_agent.Agent")
@patch("daf.bootstrap.brand_discovery_agent.LLM")
def test_agent_tools_include_archetype_and_color_tools(mock_llm: MagicMock, mock_agent: MagicMock) -> None:
    make_brand_discovery_agent("claude-sonnet-4-20250514")
    _, kwargs = mock_agent.call_args
    tool_names = {t.name for t in kwargs["tools"]}
    assert "Apply Archetype Defaults" in tool_names
    assert "Validate and Normalise Color" in tool_names
