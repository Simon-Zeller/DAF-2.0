"""Brand Discovery Agent (Agent 1, Tier 2) — task 4.1.

Architecture
------------
This module exposes three layers:

1. **Pure helper functions** (``apply_archetype_defaults``, ``resolve_color``) —
   deterministic, tested directly, no dependency on CrewAI or on a live API key.

2. **CrewAI tools** (``@tool``-decorated callables) — thin wrappers around the
   helpers that CrewAI's agent dispatch can invoke via its tool protocol.

3. **CrewAI Agent factory** (``make_brand_discovery_agent``) — returns a fully
   configured ``crewai.Agent`` bound to the Tier 2 (Sonnet) model with the tools
   above registered.  Calling this factory requires ``ANTHROPIC_API_KEY``.

Archetype default mapping
--------------------------
:Enterprise B2B:
  componentScope = "comprehensive", spacing.unit = 4, borderRadius.md = "2px",
  motion.duration.base = 200, accessibility.level = "AA"
:Consumer B2C:
  componentScope = "standard", spacing.unit = 8, borderRadius.md = "8px",
  motion.duration.base = 150, accessibility.level = "AA"
:Mobile-First:
  componentScope = "starter", spacing.unit = 8, borderRadius.md = "8px",
  motion.duration.base = 150, accessibility.level = "AA"
:Multi-Brand Platform:
  componentScope = "standard", spacing.unit = 8, borderRadius.md = "4px",
  motion.duration.base = 200, accessibility.level = "AA"
:Custom:
  No defaults applied — every field is collected explicitly via the interview.
"""

from __future__ import annotations

import json
import re
from typing import Any

from crewai import Agent, LLM
from crewai.tools import tool

# ---------------------------------------------------------------------------
# Archetype defaults
# ---------------------------------------------------------------------------

#: Maps each non-custom archetype to its default field values.
ARCHETYPE_DEFAULTS: dict[str, dict[str, Any]] = {
    "enterprise-b2b": {
        "componentScope": "comprehensive",
        "spacing": {"unit": 4},
        "borderRadius": {"md": "2px"},
        "motion": {"duration": {"base": 200}},
        "accessibility": {"level": "AA"},
    },
    "consumer-b2c": {
        "componentScope": "standard",
        "spacing": {"unit": 8},
        "borderRadius": {"md": "8px"},
        "motion": {"duration": {"base": 150}},
        "accessibility": {"level": "AA"},
    },
    "mobile-first": {
        "componentScope": "starter",
        "spacing": {"unit": 8},
        "borderRadius": {"md": "8px"},
        "motion": {"duration": {"base": 150}},
        "accessibility": {"level": "AA"},
    },
    "multi-brand-platform": {
        "componentScope": "standard",
        "spacing": {"unit": 8},
        "borderRadius": {"md": "4px"},
        "motion": {"duration": {"base": 200}},
        "accessibility": {"level": "AA"},
    },
}


def _deep_merge_defaults(target: dict[str, Any], defaults: dict[str, Any]) -> None:
    """Recursively set *defaults* values on *target* only where keys are absent."""
    for key, value in defaults.items():
        if key not in target:
            target[key] = value
        elif isinstance(value, dict) and isinstance(target[key], dict):
            _deep_merge_defaults(target[key], value)


def apply_archetype_defaults(profile: dict[str, Any]) -> dict[str, Any]:
    """Populate *profile* with archetype-appropriate defaults.

    Fields already present in *profile* are never overwritten.  The "custom"
    archetype deliberately applies no defaults.

    Parameters
    ----------
    profile:
        Partial brand profile dict — must contain an ``"archetype"`` key.

    Returns
    -------
    dict
        The same *profile* dict with default fields merged in (mutated
        in-place; also returned for convenience).
    """
    archetype = profile.get("archetype", "custom")
    defaults = ARCHETYPE_DEFAULTS.get(archetype)
    if defaults is not None:
        _deep_merge_defaults(profile, defaults)
    return profile


# ---------------------------------------------------------------------------
# Color resolution
# ---------------------------------------------------------------------------

_HEX3_RE = re.compile(r"^#?([0-9a-fA-F]{3})$")
_HEX6_RE = re.compile(r"^#?([0-9a-fA-F]{6})$")


class AmbiguousColorError(ValueError):
    """Raised when a color string cannot be unambiguously resolved to hex."""


def resolve_color(raw: str) -> str:
    """Normalise *raw* to a canonical lowercase 6-digit hex string.

    Accepts 3- or 6-digit hex, with or without a leading ``#``.

    Raises
    ------
    AmbiguousColorError
        If *raw* is empty, non-hex, or cannot be unambiguously mapped.
    """
    stripped = raw.strip()

    m6 = _HEX6_RE.match(stripped)
    if m6:
        return f"#{m6.group(1).lower()}"

    m3 = _HEX3_RE.match(stripped)
    if m3:
        digits = m3.group(1).lower()
        return f"#{''.join(c * 2 for c in digits)}"

    raise AmbiguousColorError(
        f"Cannot resolve {raw!r} to an unambiguous hex color. "
        "Provide a 3- or 6-digit hex value (e.g. #1a2b3c)."
    )


# ---------------------------------------------------------------------------
# CrewAI tools
# ---------------------------------------------------------------------------


@tool("Apply Archetype Defaults")
def apply_archetype_defaults_tool(profile_json: str) -> str:
    """Apply archetype-based defaults to a partial brand profile JSON string.

    Reads the ``archetype`` field from the profile and fills in defaults for
    ``componentScope``, ``spacing.unit``, ``borderRadius.md``,
    ``motion.duration.base``, and ``accessibility.level`` if absent.

    Returns the enriched profile as a JSON string.
    """
    profile: dict[str, Any] = json.loads(profile_json)
    result = apply_archetype_defaults(profile)
    return json.dumps(result)


@tool("Validate and Normalise Color")
def resolve_color_tool(color_input: str) -> str:
    """Validate and normalise a color input to a 6-digit lowercase hex string.

    Returns the normalised hex (e.g. ``#1a2b3c``) or an error message
    prefixed with ``ERROR:`` when the input is ambiguous.
    """
    try:
        return resolve_color(color_input)
    except AmbiguousColorError as exc:
        return f"ERROR: {exc}"


# ---------------------------------------------------------------------------
# CrewAI Agent factory
# ---------------------------------------------------------------------------


def make_brand_discovery_agent(model: str) -> Agent:
    """Build and return a ``crewai.Agent`` for brand profile discovery.

    The agent uses the Tier 2 model (Sonnet by default) and is equipped with
    tools for archetype default resolution and color normalisation.

    Parameters
    ----------
    model:
        Anthropic model identifier, e.g. ``"claude-sonnet-4-20250514"``.
        The ``"anthropic/"`` provider prefix is added automatically.

    Returns
    -------
    crewai.Agent
        Fully configured agent.  Requires ``ANTHROPIC_API_KEY`` in environment.
    """
    llm = LLM(model=f"anthropic/{model}")
    return Agent(
        role="Brand Profile Validator and Enricher",
        goal=(
            "Receive the raw brand profile from the interview CLI. "
            "Validate all fields for completeness and internal consistency. "
            "Resolve the selected archetype into concrete defaults for any "
            "unspecified fields.  Detect contradictions and fill sensible "
            "defaults.  Output the finalized, validated brand profile."
        ),
        backstory=(
            "You are an expert brand systems consultant with deep knowledge of "
            "design token architecture and component library engineering.  You "
            "have evaluated hundreds of brand profiles and understand how "
            "archetype choices cascade into downstream token and component "
            "decisions."
        ),
        llm=llm,
        tools=[apply_archetype_defaults_tool, resolve_color_tool],
        verbose=False,
    )
