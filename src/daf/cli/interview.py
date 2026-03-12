"""Brand interview conversation flow.

Conducts a structured, sequential brand interview and produces an
``InterviewResult`` data object.  All I/O is done via plain stdout/stdin so
the module is fully testable without a real terminal.

Usage (programmatic)::

    interviewer = BrandInterviewer()
    result = interviewer.run()

Usage (test-controlled)::

    interviewer = BrandInterviewer(input_lines=["Acme", "enterprise-b2b", ...])
    result = interviewer.run()
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, Optional, Sequence


# ---------------------------------------------------------------------------
# Valid vocabulary sets — exported so tests can assert on them directly
# ---------------------------------------------------------------------------

VALID_ARCHETYPES: set[str] = {
    "enterprise-b2b",
    "consumer-b2c",
    "mobile-first",
    "multi-brand-platform",
    "custom",
}

VALID_COMPONENT_SCOPES: set[str] = {"starter", "standard", "comprehensive"}

VALID_ACCESSIBILITY_LEVELS: set[str] = {"AA", "AAA"}

# ---------------------------------------------------------------------------
# Color parsing helper
# ---------------------------------------------------------------------------

_HEX_RE = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
_RGB_RE = re.compile(r"^rgb\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*\)$")
_HSL_RE = re.compile(r"^hsl\(\s*\d{1,3}\s*,\s*[\d.]+%\s*,\s*[\d.]+%\s*\)$")


def parse_color(value: str) -> str:
    """Validate and return *value* if it is a recognised color expression.

    Accepts: ``#RGB``, ``#RRGGBB``, ``rgb(…)``, ``hsl(…)``.

    Raises
    ------
    ValueError
        If *value* cannot be parsed as a valid color.
    """
    v = value.strip()
    if _HEX_RE.match(v) or _RGB_RE.match(v) or _HSL_RE.match(v):
        return v
    raise ValueError(
        f"'{v}' is not a valid color. "
        "Please enter a hex value (e.g. #0A2463), rgb(…), or hsl(…)."
    )


# ---------------------------------------------------------------------------
# Interview result
# ---------------------------------------------------------------------------

@dataclass
class InterviewResult:
    """Structured output of a completed brand interview.

    Every field maps 1-to-1 to a field in ``brand-profile.json``.
    """

    name: str
    archetype: str
    primary_color: str
    secondary_color: str
    neutral_color: str
    font_family_heading: str
    font_family_body: str
    font_scale: str
    spacing_scale: str
    component_scope: str
    border_radius: str
    elevation_scale: str
    motion_duration: str
    motion_easing: str
    breakpoints: list[str]
    accessibility_level: str
    theme_modes: list[str]
    theme_default: str
    multi_brand_names: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Interviewer
# ---------------------------------------------------------------------------

class BrandInterviewer:
    """Conducts the brand interview step by step.

    Parameters
    ----------
    input_lines:
        Optional sequence of pre-supplied answers (used in tests instead of
        actual stdin).  When *None*, prompts are read from the real terminal.
    output_lines:
        Optional list that collects all printed output (used in tests to
        inspect prompt text without capturing stdout globally).
    session_dir:
        When provided, the interviewer writes ``.daf-session.json`` to this
        directory after each completed step and deletes it on completion.
        Supports task 2.10 (interview session persistence).  If a session file
        already exists in *session_dir* the saved answers are pre-loaded so
        the interview resumes from the last completed step.
    """

    def __init__(
        self,
        input_lines: Optional[Sequence[str]] = None,
        output_lines: Optional[list[str]] = None,
        session_dir: Optional[Path] = None,
    ) -> None:
        self._input_iter: Optional[Iterator[str]] = (
            iter(input_lines) if input_lines is not None else None
        )
        self._output: list[str] = output_lines if output_lines is not None else []
        self._session_dir = session_dir

    # ------------------------------------------------------------------
    # I/O helpers
    # ------------------------------------------------------------------

    def _print(self, msg: str) -> None:
        self._output.append(msg)
        print(msg)  # noqa: T201

    def _ask(self, prompt: str) -> str:
        self._print(prompt)
        if self._input_iter is not None:
            return next(self._input_iter).strip()
        return input("> ").strip()

    def _ask_validated(self, prompt: str, valid: set[str]) -> str:
        while True:
            answer = self._ask(prompt)
            if answer in valid:
                return answer
            self._print(
                f"  Invalid choice '{answer}'. "
                f"Please choose one of: {', '.join(sorted(valid))}"
            )

    def _ask_color(self, prompt: str) -> str:
        while True:
            raw = self._ask(prompt)
            try:
                return parse_color(raw)
            except ValueError as exc:
                self._print(f"  {exc}")

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self) -> InterviewResult:
        """Run all interview steps and return the collected ``InterviewResult``."""
        from daf.cli.session import InterviewSession, load_session

        # Load any existing partial session.
        saved: Optional[InterviewSession] = None
        if self._session_dir is not None:
            saved = load_session(self._session_dir)

        # answers[i] stores the answer to step i+1 (0-indexed).
        answers: list[Optional[str]] = list(saved.answers) if saved else [None] * 19
        resume_from = (saved.last_step + 1) if saved else 1

        def _get(step: int, prompt: str) -> str:
            """Return saved answer for *step* or ask the user."""
            idx = step - 1
            if answers[idx] is not None:
                return answers[idx]  # type: ignore[return-value]
            value = self._ask(prompt)
            answers[idx] = value
            if self._session_dir is not None:
                InterviewSession(answers=list(answers), last_step=step).save(
                    self._session_dir
                )
            return value

        def _get_validated(step: int, prompt: str, valid: set[str]) -> str:
            idx = step - 1
            if answers[idx] is not None and answers[idx] in valid:
                return answers[idx]  # type: ignore[return-value]
            value = self._ask_validated(prompt, valid)
            answers[idx] = value
            if self._session_dir is not None:
                InterviewSession(answers=list(answers), last_step=step).save(
                    self._session_dir
                )
            return value

        def _get_color(step: int, prompt: str) -> str:
            idx = step - 1
            if answers[idx] is not None:
                return answers[idx]  # type: ignore[return-value]
            value = self._ask_color(prompt)
            answers[idx] = value
            if self._session_dir is not None:
                InterviewSession(answers=list(answers), last_step=step).save(
                    self._session_dir
                )
            return value

        if resume_from > 1:
            self._print(f"\n=== DAF Brand Interview (resuming from step {resume_from}) ===\n")
        else:
            self._print("\n=== DAF Brand Interview ===\n")

        name = _get(1, "1/19  Brand name:")

        archetype = _get_validated(
            2,
            "2/19  Brand archetype "
            "(enterprise-b2b / consumer-b2c / mobile-first / multi-brand-platform / custom):",
            VALID_ARCHETYPES,
        )

        primary_color = _get_color(3, "3/19  Primary colour (hex / rgb / hsl — e.g. #0A2463):")
        secondary_color = _get_color(4, "4/19  Secondary colour:")
        neutral_color = _get_color(5, "5/19  Neutral colour:")

        font_heading = _get(6, "6/19  Heading font family (e.g. Inter):")
        font_body = _get(7, "7/19  Body font family (e.g. Inter):")
        font_scale = _get(
            8, "8/19  Font scale (e.g. major-third, minor-third, perfect-fourth):"
        )

        spacing_scale = _get(9, "9/19  Base spacing unit (e.g. 4px, 8px):")

        component_scope = _get_validated(
            10,
            "10/19 Component scope (starter / standard / comprehensive):",
            VALID_COMPONENT_SCOPES,
        )

        border_radius = _get(
            11, "11/19 Border radius style (e.g. none, small, medium, large, full):"
        )
        elevation_scale = _get(12, "12/19 Elevation scale (e.g. 3-step, 5-step, flat):")
        motion_duration = _get(13, "13/19 Default motion duration (e.g. 200ms):")
        motion_easing = _get(14, "14/19 Default motion easing (e.g. ease-in-out, ease-out):")

        breakpoints_raw = _get(
            15,
            "15/19 Breakpoints as comma-separated list (e.g. sm:640px,md:768px,lg:1024px):",
        )
        breakpoints = [b.strip() for b in breakpoints_raw.split(",") if b.strip()]

        accessibility_level = _get_validated(
            16,
            "16/19 Accessibility level (AA / AAA):",
            VALID_ACCESSIBILITY_LEVELS,
        )

        theme_modes_raw = _get(
            17,
            "17/19 Theme modes as comma-separated list (e.g. light,dark,high-contrast):",
        )
        theme_modes = [t.strip() for t in theme_modes_raw.split(",") if t.strip()]

        theme_default = _get(18, "18/19 Default theme (e.g. light):")

        # Multi-brand (step 19)
        multi_brand_raw = _get(
            19, "19/19 Is this a multi-brand design system? (yes / no):"
        )
        multi_brand_names: list[str] = []
        if multi_brand_raw.strip().lower() in {"yes", "y"}:
            self._print(
                "  Enter brand identifiers one per line. "
                "Press Enter with no input when done."
            )
            while True:
                brand_id = self._ask("  Brand identifier (or Enter to finish):")
                if not brand_id:
                    break
                multi_brand_names.append(brand_id)

        self._print("\n=== Interview complete ===\n")

        # Delete session file on successful completion (spec requirement).
        if self._session_dir is not None:
            InterviewSession.delete(self._session_dir)

        return InterviewResult(
            name=name,
            archetype=archetype,
            primary_color=primary_color,
            secondary_color=secondary_color,
            neutral_color=neutral_color,
            font_family_heading=font_heading,
            font_family_body=font_body,
            font_scale=font_scale,
            spacing_scale=spacing_scale,
            component_scope=component_scope,
            border_radius=border_radius,
            elevation_scale=elevation_scale,
            motion_duration=motion_duration,
            motion_easing=motion_easing,
            breakpoints=breakpoints,
            accessibility_level=accessibility_level,
            theme_modes=theme_modes,
            theme_default=theme_default,
            multi_brand_names=multi_brand_names,
        )
