"""Tests for RollbackAgent (task 3.2).

Covers:
  - write_checkpoint: writes manifest + checksums + file snapshots
  - validate_checkpoint: detects missing or corrupted files
  - restore_checkpoint: restores files and applies cascade invalidation
  - checkpoint is stored inside .daf-checkpoints/ (consistent with resume.py)
  - .daf-checkpoints/ dir itself is NOT swept during rollback
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from daf.pipeline.rollback_agent import RollbackAgent, CheckpointIntegrityError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def write_output_files(output_dir: Path, files: dict[str, str]) -> None:
    """Create files in output_dir with given content."""
    for rel_path, content in files.items():
        p = output_dir / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")


def sha256(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()


# ---------------------------------------------------------------------------
# write_checkpoint
# ---------------------------------------------------------------------------


def test_write_checkpoint_creates_metadata_json(tmp_path: Path) -> None:
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()
    write_output_files(output_dir, {"tokens/global.tokens.json": '{"a": 1}'})

    agent = RollbackAgent()
    agent.write_checkpoint(output_dir, phase=1)

    cp_dir = output_dir / ".daf-checkpoints"
    meta_files = list(cp_dir.glob("phase-1.json"))
    assert len(meta_files) == 1


def test_write_checkpoint_manifest_lists_files(tmp_path: Path) -> None:
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()
    write_output_files(
        output_dir,
        {
            "tokens/global.tokens.json": '{"a": 1}',
            "tokens/semantic.tokens.json": '{"b": 2}',
        },
    )

    agent = RollbackAgent()
    agent.write_checkpoint(output_dir, phase=1)

    meta = json.loads((output_dir / ".daf-checkpoints" / "phase-1.json").read_text())
    assert "tokens/global.tokens.json" in meta["manifest"]
    assert "tokens/semantic.tokens.json" in meta["manifest"]


def test_write_checkpoint_checksums_are_correct(tmp_path: Path) -> None:
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()
    content = '{"token": "value"}'
    write_output_files(output_dir, {"tokens/global.tokens.json": content})

    agent = RollbackAgent()
    agent.write_checkpoint(output_dir, phase=2)

    meta = json.loads((output_dir / ".daf-checkpoints" / "phase-2.json").read_text())
    assert meta["checksums"]["tokens/global.tokens.json"] == sha256(content)


def test_write_checkpoint_copies_files_to_snapshot_dir(tmp_path: Path) -> None:
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()
    write_output_files(output_dir, {"src/Button.tsx": "export default () => null;"})

    agent = RollbackAgent()
    agent.write_checkpoint(output_dir, phase=3)

    snapshot_dir = output_dir / ".daf-checkpoints" / "phase-3"
    assert (snapshot_dir / "src" / "Button.tsx").exists()


def test_write_checkpoint_excludes_checkpoint_dir_itself(tmp_path: Path) -> None:
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()
    write_output_files(output_dir, {"tokens/global.tokens.json": "{}"})

    agent = RollbackAgent()
    agent.write_checkpoint(output_dir, phase=1)
    # Second checkpoint should not include the first checkpoint's files
    agent.write_checkpoint(output_dir, phase=2)

    meta = json.loads((output_dir / ".daf-checkpoints" / "phase-2.json").read_text())
    # No .daf-checkpoints paths should appear in the manifest
    assert not any(".daf-checkpoints" in p for p in meta["manifest"])


def test_write_checkpoint_records_phase_number(tmp_path: Path) -> None:
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()
    write_output_files(output_dir, {"brand-profile.json": "{}"})

    agent = RollbackAgent()
    agent.write_checkpoint(output_dir, phase=4)

    meta = json.loads((output_dir / ".daf-checkpoints" / "phase-4.json").read_text())
    assert meta["phase"] == 4


# ---------------------------------------------------------------------------
# validate_checkpoint
# ---------------------------------------------------------------------------


def test_validate_checkpoint_passes_when_intact(tmp_path: Path) -> None:
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()
    write_output_files(output_dir, {"tokens/global.tokens.json": '{"a": 1}'})

    agent = RollbackAgent()
    agent.write_checkpoint(output_dir, phase=1)

    # Should not raise
    agent.validate_checkpoint(output_dir, phase=1)


def test_validate_checkpoint_fails_if_file_missing(tmp_path: Path) -> None:
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()
    write_output_files(output_dir, {"tokens/global.tokens.json": '{"a": 1}'})

    agent = RollbackAgent()
    agent.write_checkpoint(output_dir, phase=1)

    # Delete the snapshot file
    (output_dir / ".daf-checkpoints" / "phase-1" / "tokens" / "global.tokens.json").unlink()

    with pytest.raises(CheckpointIntegrityError, match="missing"):
        agent.validate_checkpoint(output_dir, phase=1)


def test_validate_checkpoint_fails_if_checksum_mismatch(tmp_path: Path) -> None:
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()
    write_output_files(output_dir, {"tokens/global.tokens.json": '{"a": 1}'})

    agent = RollbackAgent()
    agent.write_checkpoint(output_dir, phase=1)

    # Corrupt the snapshot file
    snapshot = output_dir / ".daf-checkpoints" / "phase-1" / "tokens" / "global.tokens.json"
    snapshot.write_text("corrupted!", encoding="utf-8")

    with pytest.raises(CheckpointIntegrityError, match="checksum"):
        agent.validate_checkpoint(output_dir, phase=1)


def test_validate_checkpoint_fails_if_no_checkpoint(tmp_path: Path) -> None:
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()

    agent = RollbackAgent()
    with pytest.raises(CheckpointIntegrityError, match="not found"):
        agent.validate_checkpoint(output_dir, phase=1)


# ---------------------------------------------------------------------------
# restore_checkpoint
# ---------------------------------------------------------------------------


def test_restore_checkpoint_brings_back_files(tmp_path: Path) -> None:
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()
    write_output_files(output_dir, {"tokens/global.tokens.json": '{"token": "v1"}'})

    agent = RollbackAgent()
    agent.write_checkpoint(output_dir, phase=1)

    # Simulate Phase 2 writing files, then we restore Phase 1
    write_output_files(output_dir, {"tokens/compiled/variables.css": ":root {}"})

    agent.restore_checkpoint(output_dir, phase=1)

    assert (output_dir / "tokens" / "global.tokens.json").read_text() == '{"token": "v1"}'


def test_restore_checkpoint_cascade_removes_later_phase_files(tmp_path: Path) -> None:
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()
    write_output_files(output_dir, {"tokens/global.tokens.json": "{}"})

    agent = RollbackAgent()
    agent.write_checkpoint(output_dir, phase=1)

    # Phase 2 writes compiled tokens
    write_output_files(output_dir, {"tokens/compiled/variables.css": ":root {}"})
    agent.write_checkpoint(output_dir, phase=2)

    # Phase 3 writes src
    write_output_files(output_dir, {"src/Button.tsx": "const Button = () => null;"})

    # Restore to phase 1 — Phase 2+ artifacts should be removed
    agent.restore_checkpoint(output_dir, phase=1)

    assert not (output_dir / "tokens" / "compiled" / "variables.css").exists()
    assert not (output_dir / "src" / "Button.tsx").exists()


def test_restore_checkpoint_preserves_checkpoint_dir(tmp_path: Path) -> None:
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()
    write_output_files(output_dir, {"tokens/global.tokens.json": "{}"})

    agent = RollbackAgent()
    agent.write_checkpoint(output_dir, phase=1)
    agent.restore_checkpoint(output_dir, phase=1)

    # .daf-checkpoints must survive rollback
    assert (output_dir / ".daf-checkpoints").exists()


def test_restore_checkpoint_raises_on_missing_checkpoint(tmp_path: Path) -> None:
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()

    agent = RollbackAgent()
    with pytest.raises(CheckpointIntegrityError, match="not found"):
        agent.restore_checkpoint(output_dir, phase=2)


def test_restore_checkpoint_file_content_is_correct(tmp_path: Path) -> None:
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()
    content = '{"name": "MyDS"}'
    write_output_files(output_dir, {"brand-profile.json": content})

    agent = RollbackAgent()
    agent.write_checkpoint(output_dir, phase=0)

    # Overwrite the file
    (output_dir / "brand-profile.json").write_text('{"name": "CHANGED"}', encoding="utf-8")

    agent.restore_checkpoint(output_dir, phase=0)

    assert (output_dir / "brand-profile.json").read_text() == content
