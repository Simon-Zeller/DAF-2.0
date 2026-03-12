"""Interview session persistence (task 2.10).

Writes `.daf-session.json` to the output directory after each completed
interview step so that an interrupted interview can be resumed.

Lifecycle
---------
* ``InterviewSession.save(output_dir)`` — called by the interviewer after each
  step to persist the current state.
* ``discover_session(output_dir)`` — called at CLI startup to detect an
  existing in-progress session.
* ``load_session(output_dir)`` — loads and deserialises the session file.
* ``InterviewSession.delete(output_dir)`` — called after the interview
  completes and ``brand-profile.json`` is written.

The session file is intentionally a thin JSON dict (not Pydantic) to keep the
module dependency-free.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

SESSION_FILE = ".daf-session.json"

_REQUIRED_KEYS = {"answers", "last_step"}


class SessionState(Enum):
    NOT_FOUND = "not_found"
    FOUND = "found"
    CORRUPT = "corrupt"


@dataclass
class InterviewSession:
    """In-memory representation of a persisted interview session.

    Attributes
    ----------
    answers:
        19-element list of answers (or None for not-yet-answered steps).
        Index 0 corresponds to step 1.
    last_step:
        The 1-based index of the last successfully completed step.
        0 means no steps have been completed yet.
    """

    answers: list[Optional[str]] = field(default_factory=lambda: [None] * 19)
    last_step: int = 0

    @property
    def next_step(self) -> int:
        """The 1-based step number to resume from."""
        return self.last_step + 1

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, output_dir: Path) -> None:
        """Write the session to *output_dir/.daf-session.json*."""
        output_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "answers": self.answers,
            "last_step": self.last_step,
        }
        (output_dir / SESSION_FILE).write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )

    @staticmethod
    def delete(output_dir: Path) -> None:
        """Remove *output_dir/.daf-session.json* if it exists."""
        session_path = output_dir / SESSION_FILE
        if session_path.exists():
            session_path.unlink()


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def discover_session(output_dir: Path) -> SessionState:
    """Return whether a session file exists and is valid in *output_dir*."""
    session_path = output_dir / SESSION_FILE
    if not session_path.exists():
        return SessionState.NOT_FOUND

    try:
        data = json.loads(session_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return SessionState.CORRUPT

    if not _REQUIRED_KEYS.issubset(data.keys()):
        return SessionState.CORRUPT

    return SessionState.FOUND


def load_session(output_dir: Path) -> Optional[InterviewSession]:
    """Load and return the session from *output_dir*, or ``None`` on failure.

    Returns ``None`` when no file exists or the file is corrupt.
    """
    session_path = output_dir / SESSION_FILE
    if not session_path.exists():
        return None

    try:
        data = json.loads(session_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return None

    if not _REQUIRED_KEYS.issubset(data.keys()):
        return None

    try:
        return InterviewSession(
            answers=list(data["answers"]),
            last_step=int(data["last_step"]),
        )
    except (KeyError, TypeError, ValueError):
        return None
