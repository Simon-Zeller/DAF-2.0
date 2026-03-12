"""Rollback Agent (Agent 40) — checkpoint persistence and restoration.

Responsibilities
----------------
* Write a timestamped checkpoint snapshot of the entire output folder at each
  phase boundary (including a pre-Phase-1 baseline written before Phase 1 runs).
* Validate checkpoint integrity: verify every listed file is present and has a
  matching SHA-256 checksum.
* Restore a checkpoint on demand: copy snapshot files back into the output
  folder; apply cascade invalidation (remove all artifacts from phases after
  the restored checkpoint).

Checkpoint layout (inside output_dir/.daf-checkpoints/)
---------------------------------------------------------
  phase-N.json          — metadata: phase number, manifest, checksums
  phase-N/              — file snapshot: copy of every output file at phase N

The .daf-checkpoints/ directory is explicitly excluded from snapshot content
and is never removed during rollback, so checkpoints survive across restores.

This agent is organisationally grouped under Release Crew but is instantiated
at pipeline start (before Phase 1) as a cross-cutting utility.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Optional

CHECKPOINT_DIR = ".daf-checkpoints"


class CheckpointIntegrityError(RuntimeError):
    """Raised when a checkpoint is missing, corrupt, or has a checksum mismatch."""


class RollbackAgent:
    """Manages checkpoint snapshots for the DAF pipeline.

    All paths accepted and returned are absolute ``Path`` objects.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def write_checkpoint(self, output_dir: Path, phase: int) -> None:
        """Snapshot the current state of *output_dir* as a Phase *phase* checkpoint.

        Creates:
          output_dir/.daf-checkpoints/phase-N.json   — manifest + checksums
          output_dir/.daf-checkpoints/phase-N/       — file copies

        Files inside .daf-checkpoints/ are excluded from the snapshot.

        Parameters
        ----------
        output_dir:
            Absolute path to the pipeline output folder.
        phase:
            Phase number (0 = pre-Phase-1 baseline, 1–6 = post-phase boundary).
        """
        cp_dir = output_dir / CHECKPOINT_DIR
        cp_dir.mkdir(parents=True, exist_ok=True)

        snapshot_dir = cp_dir / f"phase-{phase}"
        if snapshot_dir.exists():
            shutil.rmtree(snapshot_dir)
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        manifest: list[str] = []
        checksums: dict[str, str] = {}

        for src_path in sorted(output_dir.rglob("*")):
            if not src_path.is_file():
                continue
            # Exclude the checkpoint directory itself
            try:
                rel = src_path.relative_to(output_dir)
            except ValueError:
                continue
            if rel.parts[0] == CHECKPOINT_DIR:
                continue

            rel_str = rel.as_posix()
            checksum = self._checksum(src_path)

            manifest.append(rel_str)
            checksums[rel_str] = checksum

            dest = snapshot_dir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dest)

        meta = {
            "phase": phase,
            "manifest": manifest,
            "checksums": checksums,
        }
        meta_path = cp_dir / f"phase-{phase}.json"
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    def validate_checkpoint(self, output_dir: Path, phase: int) -> None:
        """Verify the integrity of the Phase *phase* checkpoint snapshot.

        Checks that every file listed in the manifest exists in the snapshot
        directory and has a matching SHA-256 checksum.

        Raises
        ------
        CheckpointIntegrityError
            If the checkpoint metadata file is not found, a listed file is
            missing from the snapshot, or a checksum does not match.
        """
        meta = self._load_meta(output_dir, phase)
        snapshot_dir = output_dir / CHECKPOINT_DIR / f"phase-{phase}"

        missing: list[str] = []
        bad_checksums: list[str] = []

        for rel_str, expected in meta["checksums"].items():
            snap_file = snapshot_dir / rel_str
            if not snap_file.exists():
                missing.append(rel_str)
                continue
            actual = self._checksum(snap_file)
            if actual != expected:
                bad_checksums.append(rel_str)

        if missing:
            raise CheckpointIntegrityError(
                f"Phase {phase} checkpoint: {len(missing)} file(s) missing from "
                f"snapshot: {', '.join(missing[:5])}"
                + (" …" if len(missing) > 5 else "")
            )
        if bad_checksums:
            raise CheckpointIntegrityError(
                f"Phase {phase} checkpoint: checksum mismatch for "
                f"{len(bad_checksums)} file(s): {', '.join(bad_checksums[:5])}"
                + (" …" if len(bad_checksums) > 5 else "")
            )

    def restore_checkpoint(self, output_dir: Path, phase: int) -> None:
        """Restore the output folder to the state captured in Phase *phase* checkpoint.

        Steps:
        1. Validate the checkpoint integrity.
        2. Remove all non-checkpoint files from output_dir (cascade invalidation).
        3. Copy snapshot files back into output_dir.

        The .daf-checkpoints/ directory is preserved throughout.

        Raises
        ------
        CheckpointIntegrityError
            If the checkpoint cannot be validated (missing or corrupt).
        """
        # Validate before touching anything destructive
        self.validate_checkpoint(output_dir, phase)

        snapshot_dir = output_dir / CHECKPOINT_DIR / f"phase-{phase}"

        # --- Cascade invalidation: clear all non-checkpoint files ---
        for item in list(output_dir.iterdir()):
            if item.name == CHECKPOINT_DIR:
                continue
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

        # --- Restore snapshot files ---
        for src_path in sorted(snapshot_dir.rglob("*")):
            if not src_path.is_file():
                continue
            rel = src_path.relative_to(snapshot_dir)
            dest = output_dir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dest)

    def latest_checkpoint_phase(self, output_dir: Path) -> Optional[int]:
        """Return the highest complete phase number found in the checkpoint directory.

        Returns ``None`` if no valid checkpoints exist.
        """
        cp_dir = output_dir / CHECKPOINT_DIR
        if not cp_dir.exists():
            return None

        phases: list[int] = []
        for meta_file in cp_dir.glob("phase-*.json"):
            try:
                data = json.loads(meta_file.read_text(encoding="utf-8"))
                phases.append(int(data["phase"]))
            except (json.JSONDecodeError, KeyError, ValueError):
                pass

        return max(phases) if phases else None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_meta(self, output_dir: Path, phase: int) -> dict:  # type: ignore[type-arg]
        meta_path = output_dir / CHECKPOINT_DIR / f"phase-{phase}.json"
        if not meta_path.exists():
            raise CheckpointIntegrityError(
                f"Phase {phase} checkpoint not found at {meta_path}."
            )
        try:
            return json.loads(meta_path.read_text(encoding="utf-8"))  # type: ignore[no-any-return]
        except json.JSONDecodeError as exc:
            raise CheckpointIntegrityError(
                f"Phase {phase} checkpoint metadata is corrupt: {exc}"
            ) from exc

    @staticmethod
    def _checksum(path: Path) -> str:
        """Return the SHA-256 hex digest of a file's contents."""
        h = hashlib.sha256()
        h.update(path.read_bytes())
        return h.hexdigest()
