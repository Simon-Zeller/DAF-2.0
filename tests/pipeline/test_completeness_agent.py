"""Tests for Pipeline Completeness Agent (task 3.7).

Covers:
  - check_completeness: returns missing and empty file lists
  - static required files are checked
  - required non-empty directories are checked
  - results written to reports/generation-summary.json completeness section
  - non-fatal: returns result dict, does not raise
"""

from __future__ import annotations

import json
from pathlib import Path

from daf.pipeline.completeness_agent import PipelineCompletenessAgent


def write_file(output_dir: Path, rel_path: str, content: str = "content") -> None:
    p = output_dir / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def make_minimal_complete_output(output_dir: Path) -> None:
    """Write all static required files so check_completeness passes."""
    for rel in PipelineCompletenessAgent.REQUIRED_FILES:
        write_file(output_dir, rel, content='{"ok": true}')


# ---------------------------------------------------------------------------
# check_completeness
# ---------------------------------------------------------------------------


def test_all_required_files_present_returns_no_missing(tmp_path: Path) -> None:
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()
    make_minimal_complete_output(output_dir)

    agent = PipelineCompletenessAgent()
    result = agent.check_completeness(output_dir)

    assert result["missing"] == []


def test_missing_file_is_reported(tmp_path: Path) -> None:
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()
    make_minimal_complete_output(output_dir)

    # Remove one required file
    (output_dir / "reports" / "generation-summary.json").unlink()

    agent = PipelineCompletenessAgent()
    result = agent.check_completeness(output_dir)

    assert "reports/generation-summary.json" in result["missing"]


def test_empty_file_is_reported(tmp_path: Path) -> None:
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()
    make_minimal_complete_output(output_dir)

    # Make one file empty
    (output_dir / "tokens" / "compiled" / "variables.css").write_text(
        "", encoding="utf-8"
    )

    agent = PipelineCompletenessAgent()
    result = agent.check_completeness(output_dir)

    assert "tokens/compiled/variables.css" in result["empty"]


def test_result_contains_missing_and_empty_keys(tmp_path: Path) -> None:
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()

    agent = PipelineCompletenessAgent()
    result = agent.check_completeness(output_dir)

    assert "missing" in result
    assert "empty" in result


def test_multiple_missing_files_all_reported(tmp_path: Path) -> None:
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()
    make_minimal_complete_output(output_dir)

    (output_dir / "package.json").unlink()
    (output_dir / "tsconfig.json").unlink()

    agent = PipelineCompletenessAgent()
    result = agent.check_completeness(output_dir)

    assert "package.json" in result["missing"]
    assert "tsconfig.json" in result["missing"]


# ---------------------------------------------------------------------------
# write_to_summary merges completeness into generation-summary.json
# ---------------------------------------------------------------------------


def test_write_to_summary_creates_report_if_absent(tmp_path: Path) -> None:
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()
    (output_dir / "reports").mkdir()

    agent = PipelineCompletenessAgent()
    completeness = {"missing": ["package.json"], "empty": []}
    agent.write_to_summary(output_dir, completeness)

    report_path = output_dir / "reports" / "generation-summary.json"
    assert report_path.exists()
    data = json.loads(report_path.read_text())
    assert data["completeness"]["missing"] == ["package.json"]


def test_write_to_summary_merges_into_existing_report(tmp_path: Path) -> None:
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()
    reports_dir = output_dir / "reports"
    reports_dir.mkdir()
    existing = {"phase3": {"components": []}}
    (reports_dir / "generation-summary.json").write_text(
        json.dumps(existing), encoding="utf-8"
    )

    agent = PipelineCompletenessAgent()
    completeness = {"missing": [], "empty": ["docs/tokens.md"]}
    agent.write_to_summary(output_dir, completeness)

    data = json.loads((reports_dir / "generation-summary.json").read_text())
    assert data["phase3"]["components"] == []  # original preserved
    assert data["completeness"]["empty"] == ["docs/tokens.md"]


def test_is_complete_when_no_missing_or_empty(tmp_path: Path) -> None:
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()
    make_minimal_complete_output(output_dir)

    agent = PipelineCompletenessAgent()
    result = agent.check_completeness(output_dir)

    assert result["missing"] == []
    assert result["empty"] == []
