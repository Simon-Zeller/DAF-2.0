"""Task 1.4 — output folder manager tests."""

from pathlib import Path

import pytest

from daf.output.folder_manager import (
    OutputFolderError,
    OutputFolderManager,
    WriteContractViolationError,
)


# ---------------------------------------------------------------------------
# prepare()
# ---------------------------------------------------------------------------


def test_prepare_creates_directory_when_absent(tmp_path: Path) -> None:
    target = tmp_path / "new-ds"
    mgr = OutputFolderManager(target)
    mgr.prepare()
    assert target.is_dir()


def test_prepare_creates_nested_parents(tmp_path: Path) -> None:
    target = tmp_path / "a" / "b" / "c"
    mgr = OutputFolderManager(target)
    mgr.prepare()
    assert target.is_dir()


def test_prepare_existing_empty_dir_is_fine(tmp_path: Path) -> None:
    target = tmp_path / "empty"
    target.mkdir()
    mgr = OutputFolderManager(target)
    mgr.prepare()  # must not raise


def test_prepare_dirty_dir_raises_without_force_or_resume(tmp_path: Path) -> None:
    target = tmp_path / "ds"
    target.mkdir()
    (target / "brand-profile.json").write_text("{}")

    mgr = OutputFolderManager(target)
    with pytest.raises(OutputFolderError, match="already contains files"):
        mgr.prepare()


def test_prepare_dirty_dir_with_force_wipes_and_recreates(tmp_path: Path) -> None:
    target = tmp_path / "ds"
    target.mkdir()
    (target / "old-file.txt").write_text("stale")

    mgr = OutputFolderManager(target, force=True)
    mgr.prepare()

    assert target.is_dir()
    assert not (target / "old-file.txt").exists()


def test_prepare_resume_leaves_existing_files(tmp_path: Path) -> None:
    target = tmp_path / "ds"
    target.mkdir()
    existing = target / "brand-profile.json"
    existing.write_text("{}")

    mgr = OutputFolderManager(target, resume=True)
    mgr.prepare()

    assert existing.exists()


# ---------------------------------------------------------------------------
# check_write() + safe_write()
# ---------------------------------------------------------------------------


def test_check_write_allowed_path(tmp_path: Path) -> None:
    mgr = OutputFolderManager(tmp_path)
    # Should not raise
    mgr.check_write("token-engine-crew", "tokens/compiled/variables.css")


def test_check_write_disallowed_path_raises(tmp_path: Path) -> None:
    mgr = OutputFolderManager(tmp_path)
    with pytest.raises(WriteContractViolationError, match="token-engine-crew"):
        mgr.check_write("token-engine-crew", "src/components/Button.tsx")


def test_check_write_unknown_crew_raises(tmp_path: Path) -> None:
    mgr = OutputFolderManager(tmp_path)
    with pytest.raises(WriteContractViolationError, match="Unknown crew"):
        mgr.check_write("ghost-crew", "anywhere.txt")


def test_safe_write_creates_file_and_parents(tmp_path: Path) -> None:
    mgr = OutputFolderManager(tmp_path)
    path = mgr.safe_write("documentation-crew", "docs/components/Button.md", "# Button")
    assert path.read_text() == "# Button"


def test_safe_write_binary_content(tmp_path: Path) -> None:
    mgr = OutputFolderManager(tmp_path)
    path = mgr.safe_write("design-to-code-crew", "screenshots/Button--default.png", b"\x89PNG")
    assert path.read_bytes() == b"\x89PNG"


def test_safe_write_contract_violation_raises(tmp_path: Path) -> None:
    mgr = OutputFolderManager(tmp_path)
    with pytest.raises(WriteContractViolationError):
        mgr.safe_write("governance-crew", "src/index.ts", "export {}")
