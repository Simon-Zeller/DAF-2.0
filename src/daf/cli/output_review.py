"""Output Review gate — displayed after Phase 6 completes.

Shows a results summary and prompts the user for one of four actions:
  1. Accept           — pipeline is complete; accept the output
  2. Reject           — discard the output
  3. --from-phase N   — re-run from Phase N using the Phase N-1 checkpoint
  4. --retry-components Name,… — re-run Phase 3 for named components only

The gate is intentionally presentation-only: it collects a choice and returns
it to the caller (``_runner.py``).  The actual checkpoint restoration and
phase re-entry logic lives in the pipeline orchestration layer (task 3.x).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterator, Optional, Sequence


class ReviewChoice(Enum):
    ACCEPT = "accept"
    REJECT = "reject"
    FROM_PHASE = "from_phase"
    RETRY_COMPONENTS = "retry_components"


@dataclass
class ReviewSummary:
    """Data required to render the output review summary."""

    components_generated: list[str]
    components_failed: list[str]
    quality_gate_passed: bool
    quality_score: int
    exit_criteria_fatal_passed: bool
    exit_criteria_warning_count: int
    warnings: list[str] = field(default_factory=list)


@dataclass
class ReviewResult:
    """The user's decision at the output review gate."""

    choice: ReviewChoice
    from_phase: Optional[int] = None
    retry_components: list[str] = field(default_factory=list)


class OutputReviewGate:
    """Presents the Phase 6 output summary and collects the user's action.

    Parameters
    ----------
    summary:
        The ``ReviewSummary`` to display.
    input_lines:
        Optional pre-supplied answers for tests (replaces real stdin).
    """

    def __init__(
        self,
        summary: ReviewSummary,
        input_lines: Optional[Sequence[str]] = None,
    ) -> None:
        self._summary = summary
        self._input_iter: Optional[Iterator[str]] = (
            iter(input_lines) if input_lines is not None else None
        )

    # ------------------------------------------------------------------
    # Summary text
    # ------------------------------------------------------------------

    def build_summary_text(self) -> str:
        s = self._summary
        generated = ", ".join(s.components_generated) if s.components_generated else "(none)"
        failed = ", ".join(s.components_failed) if s.components_failed else "(none)"
        gate_status = "PASSED" if s.quality_gate_passed else "FAILED"
        fatal_status = "PASSED" if s.exit_criteria_fatal_passed else "FAILED"
        lines = [
            "┌─ Output Review ──────────────────────────────────────┐",
            f"  Components generated : {generated}",
            f"  Components failed    : {failed}",
            f"  Quality gate         : {gate_status} (score: {s.quality_score}/100)",
            f"  Fatal exit criteria  : {fatal_status}",
            f"  Warning count        : {s.exit_criteria_warning_count}",
        ]
        if s.warnings:
            lines.append("  Warnings:")
            for w in s.warnings:
                lines.append(f"    ⚠ {w}")
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

    def run(self) -> ReviewResult:
        """Display summary, collect and return the user's ``ReviewResult``."""
        print(self.build_summary_text())  # noqa: T201
        print(  # noqa: T201
            "\nWhat would you like to do?\n"
            "  [1] Accept — pipeline complete\n"
            "  [2] Reject — discard this output\n"
            "  [3] Re-run from phase N\n"
            "  [4] Retry specific components\n"
        )
        while True:
            raw = self._ask("Your choice (1/2/3/4):")
            if raw == "1":
                return ReviewResult(choice=ReviewChoice.ACCEPT)
            if raw == "2":
                return ReviewResult(choice=ReviewChoice.REJECT)
            if raw == "3":
                phase = self._ask_phase()
                return ReviewResult(choice=ReviewChoice.FROM_PHASE, from_phase=phase)
            if raw == "4":
                names = self._ask_component_names()
                return ReviewResult(choice=ReviewChoice.RETRY_COMPONENTS, retry_components=names)
            print(f"  Invalid choice '{raw}'. Please enter 1, 2, 3, or 4.")  # noqa: T201

    def _ask_phase(self) -> int:
        while True:
            raw = self._ask("Re-run from phase number (1–6):")
            try:
                n = int(raw)
                if 1 <= n <= 6:
                    return n
            except ValueError:
                pass
            print("  Please enter a number between 1 and 6.")  # noqa: T201

    def _ask_component_names(self) -> list[str]:
        raw = self._ask("Component names (comma-separated, e.g. Button,Modal):")
        return [name.strip() for name in raw.split(",") if name.strip()]
