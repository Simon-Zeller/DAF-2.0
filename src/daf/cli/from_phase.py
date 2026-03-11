"""--from-phase N re-entry validation (task 2.8).

Validates whether the output folder has the checkpoint required to re-start
from a given phase.  Does NOT perform any restoration — that is delegated to
the Rollback Agent (task 3.2).

Rules:
- Phase 1 is always a full restart (no prior checkpoint needed).
- Phase N (N ≥ 2) requires a valid checkpoint for Phase N-1.
- Phases outside 1–6 raise ``ValueError``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

from daf.cli.resume import CHECKPOINT_DIR, _REQUIRED_KEYS

_MIN_PHASE = 1
_MAX_PHASE = 6


class FromPhaseState(Enum):
    ready = "ready"
    missing_checkpoint = "missing_checkpoint"
    full_restart = "full_restart"

    # Convenience aliases used throughout the codebase.
    READY = "ready"
    MISSING_CHECKPOINT = "missing_checkpoint"
    FULL_RESTART = "full_restart"


@dataclass
class FromPhaseResult:
    """Result of from-phase entry validation.

    Attributes
    ----------
    state:
        READY — checkpoint found, pipeline may start from *requested_phase*.
        MISSING_CHECKPOINT — the required Phase N-1 checkpoint is absent.
        FULL_RESTART — requested Phase 1 (always valid, no prior checkpoint).
    requested_phase:
        The phase the user requested to re-enter from.
    required_checkpoint_phase:
        The phase whose checkpoint must exist before re-entry (N-1).
        ``None`` when *state* is FULL_RESTART.
    """

    state: FromPhaseState
    requested_phase: int
    required_checkpoint_phase: Optional[int]

    @property
    def message(self) -> str:
        if self.state == FromPhaseState.FULL_RESTART:
            return (
                "Phase 1 re-entry is a full restart. "
                "All existing output will be overwritten."
            )
        if self.state == FromPhaseState.READY:
            return (
                f"Ready to re-run from Phase {self.requested_phase}. "
                f"Rollback Agent will restore the Phase {self.required_checkpoint_phase} checkpoint."
            )
        # MISSING_CHECKPOINT
        return (
            f"Cannot re-enter at Phase {self.requested_phase}: "
            f"Phase {self.required_checkpoint_phase} checkpoint not found in the output folder. "
            "Run from Phase 1 instead or check the output directory."
        )


def _valid_checkpoint_phases(output_dir: Path) -> set[int]:
    """Return the set of phase numbers with a valid checkpoint on disk."""
    cp_dir = output_dir / CHECKPOINT_DIR
    if not cp_dir.exists():
        return set()

    valid: set[int] = set()
    for f in cp_dir.glob("phase-*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if _REQUIRED_KEYS.issubset(data.keys()):
                valid.add(int(data["phase"]))
        except (json.JSONDecodeError, ValueError, KeyError):
            pass
    return valid


def validate_from_phase_entry(output_dir: Path, phase: int) -> FromPhaseResult:
    """Validate whether *output_dir* satisfies the prerequisites for re-entry at *phase*.

    Parameters
    ----------
    output_dir:
        The pipeline output directory to inspect.
    phase:
        The phase number (1–6) the user wants to re-run from.

    Returns
    -------
    FromPhaseResult:
        Describing whether the entry is valid, what checkpoint is required,
        and a human-readable message.

    Raises
    ------
    ValueError:
        If *phase* is outside the range 1–6.
    """
    if not (_MIN_PHASE <= phase <= _MAX_PHASE):
        raise ValueError(f"phase must be between {_MIN_PHASE} and {_MAX_PHASE}, got {phase}")

    # Phase 1 is always a full restart — no checkpoint required.
    if phase == 1:
        return FromPhaseResult(
            state=FromPhaseState.FULL_RESTART,
            requested_phase=1,
            required_checkpoint_phase=None,
        )

    required = phase - 1
    available = _valid_checkpoint_phases(output_dir)

    if required in available:
        return FromPhaseResult(
            state=FromPhaseState.READY,
            requested_phase=phase,
            required_checkpoint_phase=required,
        )

    return FromPhaseResult(
        state=FromPhaseState.MISSING_CHECKPOINT,
        requested_phase=phase,
        required_checkpoint_phase=required,
    )
