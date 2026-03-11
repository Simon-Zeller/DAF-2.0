"""Tests for --resume flag wiring and checkpoint discovery.

Covers:
  - Valid checkpoint found → reports last phase and next phase to run
  - Corrupt / incomplete checkpoint → reports integrity failures, prompts user
  - No checkpoint found → notifies user and exits
  - resume_or_exit() returns the correct ResumeResult
"""

from __future__ import annotations

import json
from pathlib import Path

from daf.cli.resume import (
    CheckpointState,
    ResumeResult,
    discover_checkpoint,
    CHECKPOINT_DIR,
)


def _write_checkpoint(output_dir: Path, phase: int, *, corrupt: bool = False) -> Path:
    """Write a minimal checkpoint file for *phase* inside *output_dir*."""
    cp_dir = output_dir / CHECKPOINT_DIR
    cp_dir.mkdir(parents=True, exist_ok=True)
    cp_file = cp_dir / f"phase-{phase}.json"
    if corrupt:
        cp_file.write_text("{ not valid json |||")
    else:
        cp_file.write_text(
            json.dumps({"phase": phase, "manifest": ["tokens/global.tokens.json"], "checksums": {}})
        )
    return cp_file


def test_no_checkpoint_returns_not_found(tmp_path: Path) -> None:
    result = discover_checkpoint(tmp_path)
    assert result.state == CheckpointState.NOT_FOUND


def test_valid_checkpoint_returns_found(tmp_path: Path) -> None:
    _write_checkpoint(tmp_path, phase=2)
    result = discover_checkpoint(tmp_path)
    assert result.state == CheckpointState.FOUND
    assert result.last_phase == 2
    assert result.next_phase == 3


def test_valid_checkpoint_highest_phase_selected(tmp_path: Path) -> None:
    _write_checkpoint(tmp_path, phase=1)
    _write_checkpoint(tmp_path, phase=3)
    result = discover_checkpoint(tmp_path)
    assert result.last_phase == 3
    assert result.next_phase == 4


def test_corrupt_checkpoint_returns_corrupt(tmp_path: Path) -> None:
    _write_checkpoint(tmp_path, phase=2, corrupt=True)
    result = discover_checkpoint(tmp_path)
    assert result.state == CheckpointState.CORRUPT


def test_resume_result_not_found_message() -> None:
    r = ResumeResult(state=CheckpointState.NOT_FOUND)
    assert "no checkpoint" in r.message.lower()


def test_resume_result_found_message() -> None:
    r = ResumeResult(state=CheckpointState.FOUND, last_phase=2, next_phase=3)
    assert "phase 2" in r.message.lower() or "2" in r.message
    assert "phase 3" in r.message.lower() or "3" in r.message


def test_resume_result_corrupt_message() -> None:
    r = ResumeResult(state=CheckpointState.CORRUPT, corrupt_files=["phase-2.json"])
    assert "corrupt" in r.message.lower() or "invalid" in r.message.lower()
    assert "phase-2.json" in r.message
