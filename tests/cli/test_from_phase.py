"""Tests for the --from-phase re-entry validation module (task 2.8)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from daf.cli.from_phase import (
    FromPhaseState,
    validate_from_phase_entry,
)
from daf.cli.resume import CHECKPOINT_DIR


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_checkpoint(output_dir: Path, phase: int) -> None:
    """Write a minimal valid checkpoint JSON file for *phase*."""
    cp_dir = output_dir / CHECKPOINT_DIR
    cp_dir.mkdir(parents=True, exist_ok=True)
    (cp_dir / f"phase-{phase}.json").write_text(
        json.dumps({"phase": phase, "manifest": [], "checksums": {}}),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# FromPhaseState enum smoke test
# ---------------------------------------------------------------------------


def test_from_phase_state_values() -> None:
    assert FromPhaseState.READY.value == "ready"
    assert FromPhaseState.MISSING_CHECKPOINT.value == "missing_checkpoint"
    assert FromPhaseState.FULL_RESTART.value == "full_restart"


# ---------------------------------------------------------------------------
# Phase 1 — full restart (no checkpoint needed)
# ---------------------------------------------------------------------------


def test_phase_1_is_always_ready(tmp_path: Path) -> None:
    """Phase 1 re-entry is a full restart — no prior checkpoint required."""
    result = validate_from_phase_entry(tmp_path, phase=1)
    assert result.state == FromPhaseState.FULL_RESTART
    assert result.requested_phase == 1
    assert result.required_checkpoint_phase is None


# ---------------------------------------------------------------------------
# Phase N > 1 with valid prior checkpoint
# ---------------------------------------------------------------------------


def test_phase_3_with_phase_2_checkpoint_ready(tmp_path: Path) -> None:
    _make_checkpoint(tmp_path, 2)
    result = validate_from_phase_entry(tmp_path, phase=3)
    assert result.state == FromPhaseState.READY
    assert result.requested_phase == 3
    assert result.required_checkpoint_phase == 2


def test_phase_6_with_phase_5_checkpoint_ready(tmp_path: Path) -> None:
    _make_checkpoint(tmp_path, 5)
    result = validate_from_phase_entry(tmp_path, phase=6)
    assert result.state == FromPhaseState.READY
    assert result.required_checkpoint_phase == 5


def test_highest_available_checkpoint_suffices(tmp_path: Path) -> None:
    """Checkpoints for phases 2 AND 3 present — requesting phase 4 is OK."""
    _make_checkpoint(tmp_path, 2)
    _make_checkpoint(tmp_path, 3)
    result = validate_from_phase_entry(tmp_path, phase=4)
    assert result.state == FromPhaseState.READY
    assert result.required_checkpoint_phase == 3


# ---------------------------------------------------------------------------
# Phase N > 1 with MISSING prior checkpoint
# ---------------------------------------------------------------------------


def test_phase_4_no_phase_3_checkpoint_missing(tmp_path: Path) -> None:
    # Phase 2 checkpoint present but not phase 3 — requesting phase 4 fails.
    _make_checkpoint(tmp_path, 2)
    result = validate_from_phase_entry(tmp_path, phase=4)
    assert result.state == FromPhaseState.MISSING_CHECKPOINT
    assert result.required_checkpoint_phase == 3


def test_phase_2_no_phase_1_checkpoint_missing(tmp_path: Path) -> None:
    """Phase 2 needs a Phase 1 checkpoint when the dir is empty."""
    result = validate_from_phase_entry(tmp_path, phase=2)
    assert result.state == FromPhaseState.MISSING_CHECKPOINT
    assert result.required_checkpoint_phase == 1


def test_no_checkpoint_dir_missing(tmp_path: Path) -> None:
    result = validate_from_phase_entry(tmp_path, phase=3)
    assert result.state == FromPhaseState.MISSING_CHECKPOINT


# ---------------------------------------------------------------------------
# Message property
# ---------------------------------------------------------------------------


def test_message_full_restart(tmp_path: Path) -> None:
    result = validate_from_phase_entry(tmp_path, phase=1)
    assert "Phase 1" in result.message
    assert "restart" in result.message.lower()


def test_message_ready(tmp_path: Path) -> None:
    _make_checkpoint(tmp_path, 2)
    result = validate_from_phase_entry(tmp_path, phase=3)
    assert "Phase 3" in result.message
    assert "Phase 2" in result.message


def test_message_missing(tmp_path: Path) -> None:
    result = validate_from_phase_entry(tmp_path, phase=4)
    assert "Phase 3" in result.message
    assert "missing" in result.message.lower() or "not found" in result.message.lower()


# ---------------------------------------------------------------------------
# Phase range validation
# ---------------------------------------------------------------------------


def test_invalid_phase_zero_raises(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="phase"):
        validate_from_phase_entry(tmp_path, phase=0)


def test_invalid_phase_seven_raises(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="phase"):
        validate_from_phase_entry(tmp_path, phase=7)
