"""Tests for real-time progress reporter.

Covers:
  - Phase/crew/agent/retry output format
  - Phase completion summary (artifacts written, warnings)
  - Component retry inline reporting
  - Output goes to the supplied sink (no real stdout required)
"""

from __future__ import annotations

from daf.cli.progress import ProgressReporter


def test_phase_start_output() -> None:
    lines: list[str] = []
    r = ProgressReporter(sink=lines.append)
    r.phase_start(phase=2, phase_name="Token Engine Crew")
    output = "\n".join(lines)
    assert "Phase 2" in output
    assert "Token Engine Crew" in output


def test_agent_start_output() -> None:
    lines: list[str] = []
    r = ProgressReporter(sink=lines.append)
    r.agent_start(phase=2, crew="Token Engine Crew", agent="Token Validation Agent")
    output = "\n".join(lines)
    assert "Token Engine Crew" in output
    assert "Token Validation Agent" in output


def test_retry_output_includes_attempt() -> None:
    lines: list[str] = []
    r = ProgressReporter(sink=lines.append)
    r.component_retry(component="Button", attempt=2, max_attempts=3)
    output = "\n".join(lines)
    assert "Button" in output
    assert "2/3" in output


def test_phase_complete_output_lists_artifacts() -> None:
    lines: list[str] = []
    r = ProgressReporter(sink=lines.append)
    r.phase_complete(
        phase=2,
        phase_name="Token Engine Crew",
        artifacts=["variables.css", "tokens.ts"],
        warnings=[],
    )
    output = "\n".join(lines)
    assert "variables.css" in output
    assert "tokens.ts" in output


def test_phase_complete_output_lists_warnings() -> None:
    lines: list[str] = []
    r = ProgressReporter(sink=lines.append)
    r.phase_complete(
        phase=3,
        phase_name="Design-to-Code Crew",
        artifacts=[],
        warnings=["Button: missing ARIA role"],
    )
    output = "\n".join(lines)
    assert "Button: missing ARIA role" in output


def test_component_failed_output() -> None:
    lines: list[str] = []
    r = ProgressReporter(sink=lines.append)
    r.component_failed(component="Modal", reason="TypeScript compile error")
    output = "\n".join(lines)
    assert "Modal" in output
    assert "TypeScript compile error" in output


def test_sink_receives_all_lines() -> None:
    """Every reporter call must call the sink at least once."""
    calls: list[str] = []
    r = ProgressReporter(sink=calls.append)
    r.phase_start(1, "DS Bootstrap")
    r.agent_start(1, "DS Bootstrap", "Brand Discovery Agent")
    r.component_retry("Card", 1, 3)
    r.component_failed("Card", "too many retries")
    r.phase_complete(1, "DS Bootstrap", ["tokens/global.tokens.json"], [])
    assert len(calls) >= 5
