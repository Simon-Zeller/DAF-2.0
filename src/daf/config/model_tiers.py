"""Model tier configuration.

Reads DAF_TIER1_MODEL, DAF_TIER2_MODEL, DAF_TIER3_MODEL environment variables
and exposes a singleton ModelTiers instance for the pipeline to use.

Defaults:
  Tier 1 (generative agents)    — claude-sonnet-4-20250514
  Tier 2 (analytical agents)    — claude-sonnet-4-20250514
  Tier 3 (classification agents) — claude-haiku-4-20250414
"""

from __future__ import annotations

import os
from dataclasses import dataclass

# Published defaults — agents reference these constants directly in tests / docs.
TIER1_DEFAULT = "claude-sonnet-4-20250514"
TIER2_DEFAULT = "claude-sonnet-4-20250514"
TIER3_DEFAULT = "claude-haiku-4-20250414"


@dataclass(frozen=True)
class ModelTiers:
    """Immutable snapshot of the three model-tier identifiers for a pipeline run."""

    tier1: str
    """Tier 1: generative agents (code generation, composition, documentation)."""

    tier2: str
    """Tier 2: analytical agents (validation, scoring, discovery)."""

    tier3: str
    """Tier 3: classification agents (scope classification, deprecation tagging)."""


def load_model_tiers() -> ModelTiers:
    """Read model tier configuration from environment variables.

    Returns a ModelTiers with env-var overrides applied; falls back to defaults
    for any variable that is not set.
    """
    return ModelTiers(
        tier1=os.environ.get("DAF_TIER1_MODEL", TIER1_DEFAULT),
        tier2=os.environ.get("DAF_TIER2_MODEL", TIER2_DEFAULT),
        tier3=os.environ.get("DAF_TIER3_MODEL", TIER3_DEFAULT),
    )
