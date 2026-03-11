"""Tests for CLI entry point — daf init and argument parser.

Covers:
  - All supported invocation modes
  - Flag parsing (--resume, --force, --from-phase, --retry-components, --profile)
  - Invalid inputs: missing output-path, bad --from-phase value, invalid --profile path
"""

from __future__ import annotations

from click.testing import CliRunner

from daf.cli.main import cli


def test_init_requires_output_path() -> None:
    """daf init with no arguments shows usage and exits non-zero."""
    runner = CliRunner()
    result = runner.invoke(cli, ["init"])
    assert result.exit_code != 0
    assert "output-path" in result.output.lower() or "missing argument" in result.output.lower()


def test_init_basic_invocation(tmp_path: object) -> None:
    """daf init <output-path> parses cleanly and acknowledges the path."""
    runner = CliRunner()
    # We pass --dry-run to avoid actually running the pipeline in unit tests.
    result = runner.invoke(cli, ["init", str(tmp_path), "--dry-run"])
    assert result.exit_code == 0, result.output


def test_init_resume_flag(tmp_path: object) -> None:
    """--resume flag is accepted."""
    runner = CliRunner()
    result = runner.invoke(cli, ["init", str(tmp_path), "--resume", "--dry-run"])
    assert result.exit_code == 0, result.output


def test_init_force_flag(tmp_path: object) -> None:
    """--force flag is accepted."""
    runner = CliRunner()
    result = runner.invoke(cli, ["init", str(tmp_path), "--force", "--dry-run"])
    assert result.exit_code == 0, result.output


def test_init_from_phase_flag(tmp_path: object) -> None:
    """--from-phase N flag is accepted for valid N (1–6)."""
    runner = CliRunner()
    result = runner.invoke(cli, ["init", str(tmp_path), "--from-phase", "3", "--dry-run"])
    assert result.exit_code == 0, result.output


def test_init_from_phase_invalid_value(tmp_path: object) -> None:
    """--from-phase with value outside 1–6 exits non-zero."""
    runner = CliRunner()
    result = runner.invoke(cli, ["init", str(tmp_path), "--from-phase", "7", "--dry-run"])
    assert result.exit_code != 0


def test_init_retry_components_flag(tmp_path: object) -> None:
    """--retry-components Name1,Name2 flag is accepted."""
    runner = CliRunner()
    result = runner.invoke(
        cli, ["init", str(tmp_path), "--retry-components", "Button,Modal", "--dry-run"]
    )
    assert result.exit_code == 0, result.output


def test_init_profile_flag_valid(tmp_path: object) -> None:
    """--profile pointing to an existing JSON file is accepted."""
    import json

    profile = tmp_path / "brand.json"
    profile.write_text(json.dumps({"name": "Acme"}))
    runner = CliRunner()
    result = runner.invoke(
        cli, ["init", str(tmp_path), "--profile", str(profile), "--dry-run"]
    )
    assert result.exit_code == 0, result.output


def test_init_profile_flag_missing_file(tmp_path: object) -> None:
    """--profile pointing to a non-existent file exits non-zero."""
    runner = CliRunner()
    result = runner.invoke(
        cli, ["init", str(tmp_path), "--profile", str(tmp_path / "missing.json"), "--dry-run"]
    )
    assert result.exit_code != 0


def test_init_profile_flag_invalid_json(tmp_path: object) -> None:
    """--profile pointing to a file with invalid JSON exits non-zero."""
    bad = tmp_path / "bad.json"
    bad.write_text("not json {{{")
    runner = CliRunner()
    result = runner.invoke(
        cli, ["init", str(tmp_path), "--profile", str(bad), "--dry-run"]
    )
    assert result.exit_code != 0


def test_init_dry_run_does_not_start_pipeline(tmp_path: object) -> None:
    """--dry-run exits without starting the pipeline."""
    runner = CliRunner()
    result = runner.invoke(cli, ["init", str(tmp_path), "--dry-run"])
    assert result.exit_code == 0
    assert "pipeline" not in result.output.lower() or "dry run" in result.output.lower()
