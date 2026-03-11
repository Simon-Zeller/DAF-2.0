"""Internal pipeline runner — wires CLI arguments to the pipeline.

This module is the seam between the CLI argument layer and the actual pipeline
execution. Each later task (2.2–2.10, 3.x …) will add to or replace the stubs
here.  The CLI layer (main.py) remains stable; all pipeline logic lives here.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional


def run_init(
    output_path: Path,
    resume: bool,
    force: bool,
    from_phase: Optional[int],
    retry_components: Optional[str],
    profile_data: Optional[dict],  # type: ignore[type-arg]
) -> None:
    """Entry point called by ``daf init`` after argument validation.

    Placeholder implementation — full pipeline orchestration is wired in
    subsequent tasks.  Raises ``NotImplementedError`` so callers know the
    pipeline is not yet implemented.
    """
    raise NotImplementedError(
        "Pipeline execution is not yet implemented. "
        "Use --dry-run to validate arguments."
    )
