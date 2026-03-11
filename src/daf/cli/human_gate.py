"""Human Gate — Brand Profile Approval.

After the brand interview (or when a hand-written ``brand-profile.json`` is
detected), this gate displays a formatted summary and requires the user to
explicitly approve before Phase 1 begins.

Three choices:
  1. Approve       — proceed to Phase 1
  2. Re-run interview — restart the brand interview from the beginning
  3. Provide file  — exit; user will hand-write brand-profile.json and re-run

Also provides ``BrandProfileGate.load_from_file()`` to parse and validate a
hand-written brand-profile.json (fail-fast on schema errors).
"""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Iterator, Optional, Sequence

from daf.cli.brand_profile import BrandProfile


class GateChoice(Enum):
    """User's decision at the brand profile approval gate."""

    APPROVE = "approve"
    RERUN = "rerun"
    PROVIDE_FILE = "provide_file"


_CHOICE_MAP: dict[str, GateChoice] = {
    "1": GateChoice.APPROVE,
    "2": GateChoice.RERUN,
    "3": GateChoice.PROVIDE_FILE,
}


class BrandProfileGate:
    """Displays the brand profile summary and collects the user's approval choice.

    Parameters
    ----------
    profile:
        The ``BrandProfile`` to display.
    input_lines:
        Optional pre-supplied answers for tests (replaces real stdin).
    """

    def __init__(
        self,
        profile: BrandProfile,
        input_lines: Optional[Sequence[str]] = None,
    ) -> None:
        self._profile = profile
        self._input_iter: Optional[Iterator[str]] = (
            iter(input_lines) if input_lines is not None else None
        )

    # ------------------------------------------------------------------
    # Summary builder
    # ------------------------------------------------------------------

    def build_summary(self) -> str:
        """Return a human-readable text summary of the brand profile."""
        p = self._profile
        lines = [
            "┌─ Brand Profile Summary ──────────────────────────────┐",
            f"  Name            : {p.name}",
            f"  Archetype       : {p.archetype}",
            f"  Component Scope : {p.componentScope}",
            f"  Primary colour  : {p.colors.primary}",
            f"  Secondary colour: {p.colors.secondary}",
            f"  Neutral colour  : {p.colors.neutral}",
            f"  Heading font    : {p.typography.fontFamilyHeading}",
            f"  Body font       : {p.typography.fontFamilyBody}",
            f"  Font scale      : {p.typography.scale}",
            f"  Spacing base    : {p.spacing.base}",
            f"  Border radius   : {p.borderRadius}",
            f"  Elevation       : {p.elevation}",
            f"  Motion          : {p.motion.duration} / {p.motion.easing}",
            f"  Breakpoints     : {', '.join(p.breakpoints)}",
            f"  Accessibility   : {p.accessibility.level}",
            f"  Theme modes     : {', '.join(p.themes.modes)}  (default: {p.themes.default})",
        ]
        if p.themes.brands:
            lines.append(f"  Brands          : {', '.join(p.themes.brands)}")
        lines.append("└──────────────────────────────────────────────────────┘")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Gate interaction
    # ------------------------------------------------------------------

    def _ask(self, prompt: str) -> str:
        print(prompt)  # noqa: T201
        if self._input_iter is not None:
            return next(self._input_iter).strip()
        return input("> ").strip()

    def run(self) -> GateChoice:
        """Display summary, prompt for choice, return ``GateChoice``."""
        print(self.build_summary())  # noqa: T201
        print(  # noqa: T201
            "\nPlease review the brand profile above.\n"
            "  [1] Approve — proceed to Phase 1\n"
            "  [2] Re-run interview — start the brand interview again\n"
            "  [3] Provide file — exit; edit brand-profile.json manually\n"
        )
        while True:
            raw = self._ask("Your choice (1/2/3):")
            if raw in _CHOICE_MAP:
                return _CHOICE_MAP[raw]
            print(f"  Invalid choice '{raw}'. Please enter 1, 2, or 3.")  # noqa: T201

    # ------------------------------------------------------------------
    # File loader
    # ------------------------------------------------------------------

    @staticmethod
    def load_from_file(path: Path) -> BrandProfile:
        """Parse and validate *path* as a ``brand-profile.json``.

        Raises
        ------
        FileNotFoundError
            If *path* does not exist.
        pydantic.ValidationError
            If the file content does not match the ``BrandProfile`` schema.
        json.JSONDecodeError
            If the file contains invalid JSON.
        """
        if not path.exists():
            raise FileNotFoundError(f"brand-profile.json not found at: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        return BrandProfile(**data)
