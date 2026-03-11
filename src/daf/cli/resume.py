"""Resume flag wiring — checkpoint discovery and integrity validation.

This module provides the client-side view of the resume mechanism.  The
Rollback Agent (task 3.2) is responsible for actually writing and restoring
checkpoints.  This module:

1. Scans *output_dir/.daf-checkpoints/* for checkpoint files.
2. Validates each file (readable, valid JSON, expected keys present).
3. Returns a ``ResumeResult`` that the CLI layer uses to decide whether to
   proceed, warn, or abort.

The actual checkpoint restoration is delegated to the Rollback Agent at
pipeline start (task 3.2).  This file is intentionally thin: it only
discovers and reports — it does not restore.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

# Subdirectory inside the output folder where checkpoint files live.
CHECKPOINT_DIR = ".daf-checkpoints"

_REQUIRED_KEYS = {"phase", "manifest", "checksums"}


class CheckpointState(Enum):
    NOT_FOUND = "not_found"
    FOUND = "found"
    CORRUPT = "corrupt"


@dataclass
class ResumeResult:
    """Result of checkpoint discovery.

    Attributes
    ----------
    state:
        Whether a valid checkpoint was found, none was found, or the found
        checkpoint is corrupt / unreadable.
    last_phase:
        The highest complete phase found in a valid checkpoint (only set when
        ``state == FOUND``).
    next_phase:
        The phase to re-run from (``last_phase + 1``, only set when
        ``state == FOUND``).
    corrupt_files:
        List of filenames that failed validation (only set when
        ``state == CORRUPT``).
    message:
        Human-readable summary string shown to the user by the CLI.
    """

    state: CheckpointState
    last_phase: Optional[int] = None
    next_phase: Optional[int] = None
    corrupt_files: list[str] = field(default_factory=list)

    @property
    def message(self) -> str:
        if self.state == CheckpointState.NOT_FOUND:
            return (
                "No checkpoint found in the output folder. "
                "Cannot resume — no previous run detected."
            )
        if self.state == CheckpointState.FOUND:
            return (
                f"Resuming from Phase {self.last_phase} checkpoint. "
                f"Next phase to run: Phase {self.next_phase}."
            )
        # CORRUPT
        files = ", ".join(self.corrupt_files) if self.corrupt_files else "unknown"
        return (
            f"Checkpoint integrity failure — invalid or corrupt files: {files}. "
            "Please restart from Phase 1 or remove the corrupt checkpoint files."
        )


def discover_checkpoint(output_dir: Path) -> ResumeResult:
    """Scan *output_dir* for checkpoint files and return a ``ResumeResult``.

    Does NOT restore any checkpoint — restoration is handled by the Rollback
    Agent (task 3.2).

    Parameters
    ----------
    output_dir:
        The pipeline output directory to scan.

    Returns
    -------
    ResumeResult
        Describing what was found (NOT_FOUND, FOUND, or CORRUPT).
    """
    cp_dir = output_dir / CHECKPOINT_DIR
    if not cp_dir.exists():
        return ResumeResult(state=CheckpointState.NOT_FOUND)

    cp_files = sorted(cp_dir.glob("phase-*.json"))
    if not cp_files:
        return ResumeResult(state=CheckpointState.NOT_FOUND)

    valid: list[tuple[int, Path]] = []
    corrupt: list[str] = []

    for f in cp_files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if not _REQUIRED_KEYS.issubset(data.keys()):
                corrupt.append(f.name)
                continue
            phase = int(data["phase"])
            valid.append((phase, f))
        except (json.JSONDecodeError, ValueError, KeyError):
            corrupt.append(f.name)

    if corrupt and not valid:
        return ResumeResult(state=CheckpointState.CORRUPT, corrupt_files=corrupt)

    if not valid:
        return ResumeResult(state=CheckpointState.NOT_FOUND)

    last_phase = max(p for p, _ in valid)
    return ResumeResult(
        state=CheckpointState.FOUND,
        last_phase=last_phase,
        next_phase=last_phase + 1,
        corrupt_files=corrupt,
    )
