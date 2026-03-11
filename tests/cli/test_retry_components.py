"""Tests for the --retry-components re-entry validation module (task 2.9)."""

from __future__ import annotations

import json
from pathlib import Path

from daf.cli.retry_components import (
    RetryComponentsState,
    validate_retry_components_entry,
)
from daf.cli.resume import CHECKPOINT_DIR


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_checkpoint(output_dir: Path, phase: int) -> None:
    cp_dir = output_dir / CHECKPOINT_DIR
    cp_dir.mkdir(parents=True, exist_ok=True)
    (cp_dir / f"phase-{phase}.json").write_text(
        json.dumps({"phase": phase, "manifest": [], "checksums": {}}),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# RetryComponentsState enum smoke test
# ---------------------------------------------------------------------------


def test_state_values() -> None:
    assert RetryComponentsState.READY.value == "ready"
    assert RetryComponentsState.MISSING_CHECKPOINT.value == "missing_checkpoint"
    assert RetryComponentsState.EMPTY_LIST.value == "empty_list"


# ---------------------------------------------------------------------------
# Happy path — valid components + Phase 2 & Phase 3 checkpoints
# ---------------------------------------------------------------------------


def test_ready_with_phase_2_and_3_checkpoints(tmp_path: Path) -> None:
    """Retry requires Phase 2 checkpoint (end of token generation) and Phase 3."""
    _make_checkpoint(tmp_path, 2)
    _make_checkpoint(tmp_path, 3)
    result = validate_retry_components_entry(tmp_path, ["Button", "Modal"])
    assert result.state == RetryComponentsState.READY
    assert result.components == ["Button", "Modal"]


def test_ready_single_component(tmp_path: Path) -> None:
    _make_checkpoint(tmp_path, 2)
    _make_checkpoint(tmp_path, 3)
    result = validate_retry_components_entry(tmp_path, ["Card"])
    assert result.state == RetryComponentsState.READY
    assert result.components == ["Card"]


def test_components_are_deduplicated(tmp_path: Path) -> None:
    _make_checkpoint(tmp_path, 2)
    _make_checkpoint(tmp_path, 3)
    result = validate_retry_components_entry(tmp_path, ["Button", "Button", "Modal"])
    assert result.components == ["Button", "Modal"]


def test_component_names_are_stripped(tmp_path: Path) -> None:
    _make_checkpoint(tmp_path, 2)
    _make_checkpoint(tmp_path, 3)
    result = validate_retry_components_entry(tmp_path, ["  Button  ", " Modal"])
    assert result.state == RetryComponentsState.READY
    assert "Button" in result.components
    assert "Modal" in result.components


# ---------------------------------------------------------------------------
# Missing checkpoint scenarios
# ---------------------------------------------------------------------------


def test_missing_phase_2_checkpoint(tmp_path: Path) -> None:
    """No Phase 2 checkpoint means we cannot retry components."""
    _make_checkpoint(tmp_path, 3)
    result = validate_retry_components_entry(tmp_path, ["Button"])
    assert result.state == RetryComponentsState.MISSING_CHECKPOINT


def test_missing_phase_3_checkpoint(tmp_path: Path) -> None:
    """No Phase 3 checkpoint means Phase 3 never completed."""
    _make_checkpoint(tmp_path, 2)
    result = validate_retry_components_entry(tmp_path, ["Button"])
    assert result.state == RetryComponentsState.MISSING_CHECKPOINT


def test_no_checkpoints_at_all(tmp_path: Path) -> None:
    result = validate_retry_components_entry(tmp_path, ["Button"])
    assert result.state == RetryComponentsState.MISSING_CHECKPOINT


def test_no_checkpoint_dir(tmp_path: Path) -> None:
    result = validate_retry_components_entry(tmp_path, ["Modal"])
    assert result.state == RetryComponentsState.MISSING_CHECKPOINT


# ---------------------------------------------------------------------------
# Empty / blank component list
# ---------------------------------------------------------------------------


def test_empty_list_returns_empty_list_state(tmp_path: Path) -> None:
    _make_checkpoint(tmp_path, 2)
    _make_checkpoint(tmp_path, 3)
    result = validate_retry_components_entry(tmp_path, [])
    assert result.state == RetryComponentsState.EMPTY_LIST


def test_blank_names_only_returns_empty_list_state(tmp_path: Path) -> None:
    _make_checkpoint(tmp_path, 2)
    _make_checkpoint(tmp_path, 3)
    result = validate_retry_components_entry(tmp_path, ["  ", ""])
    assert result.state == RetryComponentsState.EMPTY_LIST


# ---------------------------------------------------------------------------
# Message property
# ---------------------------------------------------------------------------


def test_message_ready(tmp_path: Path) -> None:
    _make_checkpoint(tmp_path, 2)
    _make_checkpoint(tmp_path, 3)
    result = validate_retry_components_entry(tmp_path, ["Button", "Modal"])
    assert "Button" in result.message
    assert "Modal" in result.message
    assert "Phase 3" in result.message


def test_message_missing_checkpoint(tmp_path: Path) -> None:
    result = validate_retry_components_entry(tmp_path, ["Button"])
    assert "Phase 2" in result.message or "Phase 3" in result.message
    assert "checkpoint" in result.message.lower() or "not found" in result.message.lower()


def test_message_empty_list(tmp_path: Path) -> None:
    _make_checkpoint(tmp_path, 2)
    _make_checkpoint(tmp_path, 3)
    result = validate_retry_components_entry(tmp_path, [])
    assert "component" in result.message.lower()
