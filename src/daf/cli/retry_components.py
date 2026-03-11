"""--retry-components Name1,... re-entry validation (task 2.9).

Validates whether the output folder has the checkpoints required to retry
specific components in Phase 3, then re-run Phase 4–6.

Rules:
- Requires both a Phase 2 checkpoint (tokens / primitives intact) and a
  Phase 3 checkpoint (Design-to-Code completed at least once).
- Component names are stripped of whitespace and deduplicated (order preserved).
- An empty or all-blank component list returns EMPTY_LIST.
- Does NOT perform any pipeline execution — that is delegated to the pipeline
  runner (task 3.x).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from daf.cli.from_phase import _valid_checkpoint_phases

# Both of these checkpoints must be present for a targeted component retry.
_REQUIRED_CHECKPOINT_PHASES = {2, 3}


class RetryComponentsState(Enum):
    READY = "ready"
    MISSING_CHECKPOINT = "missing_checkpoint"
    EMPTY_LIST = "empty_list"


@dataclass
class RetryComponentsResult:
    """Result of retry-components entry validation.

    Attributes
    ----------
    state:
        READY — prerequisites satisfied, retry may proceed.
        MISSING_CHECKPOINT — Phase 2 or Phase 3 checkpoint is absent.
        EMPTY_LIST — no valid component names were provided.
    components:
        Deduplicated, stripped list of component names to retry.
        Empty list when *state* is not READY.
    """

    state: RetryComponentsState
    components: list[str] = field(default_factory=list)

    @property
    def message(self) -> str:
        if self.state == RetryComponentsState.READY:
            names = ", ".join(self.components)
            return (
                f"Ready to retry components [{names}] in Phase 3, "
                "then re-run Phase 4–6."
            )
        if self.state == RetryComponentsState.MISSING_CHECKPOINT:
            return (
                "Cannot retry components: Phase 2 and Phase 3 checkpoints must both "
                "be present in the output folder. Run the full pipeline first."
            )
        # EMPTY_LIST
        return (
            "No component names provided. "
            "Specify at least one component name to retry."
        )


def validate_retry_components_entry(
    output_dir: Path,
    components: list[str],
) -> RetryComponentsResult:
    """Validate prerequisites for a targeted component retry.

    Parameters
    ----------
    output_dir:
        The pipeline output directory to inspect.
    components:
        Raw list of component names (may include whitespace/duplicates).

    Returns
    -------
    RetryComponentsResult:
        Describing whether the retry is valid and the cleaned component list.
    """
    # Normalise component names first (strip + remove blanks + deduplicate).
    seen: set[str] = set()
    clean: list[str] = []
    for name in components:
        stripped = name.strip()
        if stripped and stripped not in seen:
            seen.add(stripped)
            clean.append(stripped)

    if not clean:
        return RetryComponentsResult(state=RetryComponentsState.EMPTY_LIST)

    available = _valid_checkpoint_phases(output_dir)
    if not _REQUIRED_CHECKPOINT_PHASES.issubset(available):
        return RetryComponentsResult(state=RetryComponentsState.MISSING_CHECKPOINT)

    return RetryComponentsResult(
        state=RetryComponentsState.READY,
        components=clean,
    )
