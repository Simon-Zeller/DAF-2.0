"""Tests for Output Review gate (post-Phase 6).

Covers:
  - Summary display (components generated/failed, quality gate results, exit criteria, warnings)
  - Four actions: Accept / Reject / --from-phase N / --retry-components
  - Re-prompting on invalid input
  - ReviewChoice enum values
"""

from __future__ import annotations

from daf.cli.output_review import (
    OutputReviewGate,
    ReviewChoice,
    ReviewSummary,
)


def _make_summary() -> ReviewSummary:
    return ReviewSummary(
        components_generated=["Button", "Input", "Card"],
        components_failed=["Modal"],
        quality_gate_passed=True,
        quality_score=82,
        exit_criteria_fatal_passed=True,
        exit_criteria_warning_count=1,
        warnings=["Modal marked as failed"],
    )


def test_summary_contains_generated_components() -> None:
    gate = OutputReviewGate(summary=_make_summary(), input_lines=["1"])
    text = gate.build_summary_text()
    assert "Button" in text
    assert "Input" in text
    assert "Card" in text


def test_summary_contains_failed_components() -> None:
    gate = OutputReviewGate(summary=_make_summary(), input_lines=["1"])
    text = gate.build_summary_text()
    assert "Modal" in text


def test_summary_contains_quality_score() -> None:
    gate = OutputReviewGate(summary=_make_summary(), input_lines=["1"])
    text = gate.build_summary_text()
    assert "82" in text


def test_summary_contains_warnings() -> None:
    gate = OutputReviewGate(summary=_make_summary(), input_lines=["1"])
    text = gate.build_summary_text()
    assert "Modal marked as failed" in text


def test_accept_returns_accept() -> None:
    gate = OutputReviewGate(summary=_make_summary(), input_lines=["1"])
    result = gate.run()
    assert result.choice == ReviewChoice.ACCEPT


def test_reject_returns_reject() -> None:
    gate = OutputReviewGate(summary=_make_summary(), input_lines=["2"])
    result = gate.run()
    assert result.choice == ReviewChoice.REJECT


def test_from_phase_prompts_for_n() -> None:
    """Choosing from-phase prompts for phase number, returns FROM_PHASE with value."""
    gate = OutputReviewGate(summary=_make_summary(), input_lines=["3", "4"])
    result = gate.run()
    assert result.choice == ReviewChoice.FROM_PHASE
    assert result.from_phase == 4


def test_retry_components_prompts_for_names() -> None:
    """Choosing retry-components prompts for names, returns RETRY_COMPONENTS with list."""
    gate = OutputReviewGate(summary=_make_summary(), input_lines=["4", "Button,Modal"])
    result = gate.run()
    assert result.choice == ReviewChoice.RETRY_COMPONENTS
    assert result.retry_components == ["Button", "Modal"]


def test_invalid_choice_reprompts() -> None:
    gate = OutputReviewGate(summary=_make_summary(), input_lines=["x", "99", "1"])
    result = gate.run()
    assert result.choice == ReviewChoice.ACCEPT


def test_from_phase_invalid_value_reprompts() -> None:
    """Invalid phase number (outside 1–6) is re-prompted."""
    gate = OutputReviewGate(summary=_make_summary(), input_lines=["3", "9", "3"])
    result = gate.run()
    assert result.choice == ReviewChoice.FROM_PHASE
    assert result.from_phase == 3
