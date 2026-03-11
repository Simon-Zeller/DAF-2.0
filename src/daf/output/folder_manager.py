"""Shared output folder manager.

Responsibilities
----------------
* Create the output directory on first use (including parent dirs).
* On a non-resume, non-force run detect an already-populated directory and
  prompt the user to confirm before wiping it.
* Enforce per-crew file write contracts — a crew may only write to paths
  inside its declared set of allowed prefixes.
* Provide a safe, contract-checked ``write`` helper used by all crews.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Sequence

# ---------------------------------------------------------------------------
# Per-crew file write contracts
# ---------------------------------------------------------------------------
# Keys match the crew identifiers used in pipeline-config.json.
# Values are path prefixes (relative to the output root) a crew is permitted
# to write.  A crew that attempts to write outside its declared prefixes will
# get a WriteContractViolationError — caught in tests and integration runs.
# ---------------------------------------------------------------------------

CREW_WRITE_CONTRACTS: dict[str, Sequence[str]] = {
    "ds-bootstrap-crew": [
        "tokens/global.tokens.json",
        "tokens/semantic.tokens.json",
        "tokens/component.tokens.json",
        "tokens/brands/",
        "specs/",
        "tsconfig.json",
        "vite.config.ts",
        "vitest.config.ts",
        "pipeline-config.json",
        "brand-profile.json",
    ],
    "token-engine-crew": [
        "tokens/compiled/",
        "tokens/diff.json",
        "reports/token-integrity.json",
    ],
    "design-to-code-crew": [
        "src/primitives/",
        "src/components/",
        "screenshots/",
        "reports/generation-summary.json",
    ],
    "component-factory-crew": [
        "src/primitives/",
        "src/components/",
        "reports/quality-scorecard.json",
        "reports/a11y-audit.json",
        "reports/composition-audit.json",
    ],
    "documentation-crew": [
        "docs/",
    ],
    "governance-crew": [
        "governance/",
        "tests/",
    ],
    "ai-semantic-layer-crew": [
        "registry/",
        ".cursorrules",
        "copilot-instructions.md",
        "ai-context.json",
    ],
    "analytics-crew": [
        "reports/token-compliance.json",
        "reports/usage-report.json",
        "reports/drift-report.json",
        "reports/breakage-correlation.json",
        "reports/composition-audit.json",
    ],
    "release-crew": [
        "package.json",
        "src/index.ts",
        "src/primitives/index.ts",
        "src/components/index.ts",
        "docs/changelog.md",
        "docs/migration/",
        "reports/generation-summary.json",
    ],
}


class OutputFolderError(RuntimeError):
    """Base error for output folder manager failures."""


class WriteContractViolationError(OutputFolderError):
    """Raised when a crew attempts to write a path outside its allowed set."""


class OutputFolderManager:
    """Manages the shared output folder for a DAF pipeline run.

    Parameters
    ----------
    root:
        Absolute path to the output directory.
    resume:
        ``True`` when the CLI was invoked with ``--resume``.  Skips the
        dirty-directory check.
    force:
        ``True`` when the CLI was invoked with ``--force``.  Wipes an existing
        directory without prompting.
    """

    def __init__(self, root: Path, *, resume: bool = False, force: bool = False) -> None:
        self.root = root.resolve()
        self._resume = resume
        self._force = force

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def prepare(self) -> None:
        """Create or validate the output directory.

        * If the directory does not exist → create it.
        * If it exists and is empty → proceed.
        * If it exists and contains files AND ``--resume`` is not set:
          - With ``--force``: wipe and recreate silently.
          - Without ``--force``: raise :class:`OutputFolderError` with a
            message the CLI layer should display to the user before prompting
            for confirmation.

        Call this once at pipeline startup, before Phase 1 begins.
        """
        if not self.root.exists():
            self.root.mkdir(parents=True, exist_ok=True)
            return

        if self._resume:
            # Resume mode: leave existing artifacts untouched; the Rollback
            # Agent is responsible for restoring the correct checkpoint.
            return

        if self._is_dirty():
            if self._force:
                self._wipe()
            else:
                raise OutputFolderError(
                    f"Output directory '{self.root}' already contains files from "
                    "a previous run.\n"
                    "Options:\n"
                    "  • Re-run with --force to overwrite\n"
                    "  • Re-run with --resume to continue from the last checkpoint\n"
                    "  • Choose a different output path"
                )

    def wipe(self) -> None:
        """Unconditionally remove and recreate the output directory.

        Used by the Rollback Agent after the user confirms the overwrite prompt.
        """
        self._wipe()

    # ------------------------------------------------------------------
    # File write contract enforcement
    # ------------------------------------------------------------------

    def check_write(self, crew_id: str, relative_path: str) -> None:
        """Assert that *crew_id* is allowed to write *relative_path*.

        Parameters
        ----------
        crew_id:
            The crew identifier as defined in ``pipeline-config.json``.
        relative_path:
            Path relative to the output root that the crew intends to write.

        Raises
        ------
        WriteContractViolationError
            If the path is not covered by the crew's declared write prefixes.
        """
        allowed = CREW_WRITE_CONTRACTS.get(crew_id)
        if allowed is None:
            raise WriteContractViolationError(
                f"Unknown crew '{crew_id}' — no write contract defined."
            )

        normalized = relative_path.lstrip("/")
        for prefix in allowed:
            if normalized == prefix or normalized.startswith(prefix):
                return

        raise WriteContractViolationError(
            f"Crew '{crew_id}' is not permitted to write '{relative_path}'. "
            f"Allowed prefixes: {list(allowed)}"
        )

    def safe_write(self, crew_id: str, relative_path: str, content: str | bytes) -> Path:
        """Write *content* to *relative_path* after checking the write contract.

        Creates intermediate directories as needed.

        Returns the absolute path that was written.
        """
        self.check_write(crew_id, relative_path)
        target = self.root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            target.write_bytes(content)
        else:
            target.write_text(content, encoding="utf-8")
        return target

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _is_dirty(self) -> bool:
        """Return True if the output directory contains any files."""
        if not self.root.exists():
            return False
        return any(self.root.iterdir())

    def _wipe(self) -> None:
        shutil.rmtree(self.root)
        self.root.mkdir(parents=True, exist_ok=True)
