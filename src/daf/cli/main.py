"""CLI entry point for DAF — Design Automation Framework.

Primary command: ``daf init <output-path>``

Supported flags:
  --resume                    Resume from the most recent valid checkpoint.
  --force                     Overwrite existing output folder without prompting.
  --from-phase N              Re-run pipeline from Phase N (1–6).
  --retry-components Name,…   Re-run Phase 3 for named components only.
  --profile <path>            Load a pre-written brand-profile.json; skip interview.
  --dry-run                   Parse and validate arguments then exit; do not run pipeline.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import click


@click.group()
def cli() -> None:
    """DAF — Design Automation Framework."""


@cli.command()
@click.argument("output_path", metavar="output-path", type=click.Path())
@click.option(
    "--resume",
    is_flag=True,
    default=False,
    help="Resume from the most recent valid checkpoint in the output folder.",
)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Overwrite an existing non-empty output folder without prompting.",
)
@click.option(
    "--from-phase",
    "from_phase",
    type=int,
    default=None,
    metavar="N",
    help="Re-run the pipeline from Phase N onward (1–6).",
)
@click.option(
    "--retry-components",
    "retry_components",
    type=str,
    default=None,
    metavar="Name1,Name2,...",
    help="Re-run Phase 3 for named components only, then re-run Phase 4–6.",
)
@click.option(
    "--profile",
    "profile_path",
    type=click.Path(),
    default=None,
    metavar="path",
    help="Path to a pre-written brand-profile.json; skips the brand interview.",
)
@click.option(
    "--dry-run",
    "dry_run",
    is_flag=True,
    default=False,
    hidden=True,
    help="Validate arguments and exit without starting the pipeline.",
)
def init(
    output_path: str,
    resume: bool,
    force: bool,
    from_phase: Optional[int],
    retry_components: Optional[str],
    profile_path: Optional[str],
    dry_run: bool,
) -> None:
    """Initialise a new design system at OUTPUT-PATH.

    Run the full brand interview and pipeline, or provide a brand-profile.json
    with --profile to skip the interview.
    """
    # Validate --from-phase range before anything else.
    if from_phase is not None and not (1 <= from_phase <= 6):
        raise click.UsageError(
            f"--from-phase must be between 1 and 6, got {from_phase}."
        )

    # Validate --profile file exists and contains valid JSON.
    profile_data: Optional[dict] = None  # type: ignore[type-arg]
    if profile_path is not None:
        p = Path(profile_path)
        if not p.exists():
            raise click.UsageError(f"--profile file not found: {profile_path}")
        try:
            profile_data = json.loads(p.read_text())
        except json.JSONDecodeError as exc:
            raise click.UsageError(
                f"--profile file contains invalid JSON: {exc}"
            ) from exc

    out = Path(output_path)

    if dry_run:
        click.echo(
            f"[dry run] daf init {out} "
            f"resume={resume} force={force} "
            f"from_phase={from_phase} "
            f"retry_components={retry_components} "
            f"profile={'<loaded>' if profile_data is not None else None}"
        )
        return

    # --- pipeline entry point (to be wired up in later tasks) ---
    from daf.cli._runner import run_init  # noqa: PLC0415

    run_init(
        output_path=out,
        resume=resume,
        force=force,
        from_phase=from_phase,
        retry_components=retry_components,
        profile_data=profile_data,
    )
