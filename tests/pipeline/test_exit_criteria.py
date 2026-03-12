"""Tests for exit criteria enforcement (task 3.8).

Covers the 15 exit criteria (8 Fatal + 7 Warning) as defined in the spec.
Verifies:
  - Fatal failure prevents isComplete: True
  - Warning failure allows isComplete: True but surfaces in output
  - All 15 criteria written to exitCriteria in generation-summary.json
  - allFatalPassed / warningCount / isComplete fields are correct
"""

from __future__ import annotations

import json
from pathlib import Path

from daf.pipeline.exit_criteria import (
    CriteriaResult,
    ExitCriteriaChecker,
    ExitCriteriaSeverity,
    ExitCriteriaStatus,
)


def write_file(output_dir: Path, rel: str, content: str = "ok") -> None:
    p = output_dir / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# CriteriaResult
# ---------------------------------------------------------------------------


def test_criteria_result_fatal_sets_severity() -> None:
    r = CriteriaResult(
        criterion_id=1,
        description="Token JSON parses",
        severity=ExitCriteriaSeverity.FATAL,
        status=ExitCriteriaStatus.PASSED,
        details=None,
    )
    assert r.severity == ExitCriteriaSeverity.FATAL
    assert r.status == ExitCriteriaStatus.PASSED


def test_criteria_result_warning_severity() -> None:
    r = CriteriaResult(
        criterion_id=9,
        description="All unit tests pass",
        severity=ExitCriteriaSeverity.WARNING,
        status=ExitCriteriaStatus.FAILED,
        details="2 tests failing",
    )
    assert r.severity == ExitCriteriaSeverity.WARNING
    assert r.status == ExitCriteriaStatus.FAILED


# ---------------------------------------------------------------------------
# ExitCriteriaChecker.evaluate_from_summary
# ---------------------------------------------------------------------------

def _make_default_summary() -> dict:  # type: ignore[type-arg]
    """Return a generation summary dict where all 15 criteria pass."""
    return {
        # Token criteria (1–4): all files parseable + valid DTCG
        "tokensParseable": True,
        "tokensDtcgValid": True,
        "semanticRefsResolve": True,
        "componentRefsResolve": True,
        # WCAG (5)
        "wcagContrastPassed": True,
        # CSS undefined refs (6)
        "cssUndefinedRefs": False,
        # TypeScript (7)
        "typescriptErrors": 0,
        # Build (8)
        "hasBuildFailure": False,
        # Test failures (9 - warning)
        "hasTestFailures": False,
        # Hardcoded values (10 - warning)
        "hardcodedValuesDetected": False,
        # ARIA roles (11 - warning)
        "interactiveComponentsMissingAria": False,
        # Quality gate score (12 - warning)
        "qualityGateBelowThreshold": False,
        # Drift (13 - warning)
        "specCodeDocsDriftDetected": False,
        # Registry valid (14 - warning)
        "registryIncomplete": False,
        # Failed components (15 - warning)
        "failedComponents": [],
    }


def test_all_criteria_pass_sets_is_complete(tmp_path: Path) -> None:
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()
    (output_dir / "dist").mkdir()
    write_file(output_dir, "dist/index.js", "/* built */")

    checker = ExitCriteriaChecker()
    summary = _make_default_summary()
    result = checker.evaluate_from_summary(summary, output_dir)

    assert result["isComplete"] is True
    assert result["allFatalPassed"] is True
    assert result["warningCount"] == 0


def test_fatal_failure_prevents_is_complete(tmp_path: Path) -> None:
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()

    checker = ExitCriteriaChecker()
    summary = _make_default_summary()
    summary["hasBuildFailure"] = True  # Fatal criterion 8

    result = checker.evaluate_from_summary(summary, output_dir)

    assert result["isComplete"] is False
    assert result["allFatalPassed"] is False


def test_warning_failure_allows_is_complete(tmp_path: Path) -> None:
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()
    (output_dir / "dist").mkdir()
    write_file(output_dir, "dist/index.js", "/* built */")

    checker = ExitCriteriaChecker()
    summary = _make_default_summary()
    summary["hasTestFailures"] = True  # Warning criterion 9

    result = checker.evaluate_from_summary(summary, output_dir)

    assert result["isComplete"] is True
    assert result["warningCount"] >= 1


def test_result_contains_all_15_criteria(tmp_path: Path) -> None:
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()

    checker = ExitCriteriaChecker()
    summary = _make_default_summary()
    result = checker.evaluate_from_summary(summary, output_dir)

    assert len(result["criteria"]) == 15


def test_failed_components_warning_increments_warning_count(tmp_path: Path) -> None:
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()
    (output_dir / "dist").mkdir()
    write_file(output_dir, "dist/index.js", "/* built */")

    checker = ExitCriteriaChecker()
    summary = _make_default_summary()
    summary["failedComponents"] = ["Button"]  # Warning criterion 15

    result = checker.evaluate_from_summary(summary, output_dir)

    assert result["isComplete"] is True
    assert result["warningCount"] >= 1


def test_typescript_errors_triggers_fatal(tmp_path: Path) -> None:
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()

    checker = ExitCriteriaChecker()
    summary = _make_default_summary()
    summary["typescriptErrors"] = 3  # Fatal criterion 7

    result = checker.evaluate_from_summary(summary, output_dir)

    assert result["isComplete"] is False
    assert result["allFatalPassed"] is False


def test_dist_empty_triggers_build_failure_fatal(tmp_path: Path) -> None:
    """Criterion 8: dist/ must be non-empty after build."""
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()
    (output_dir / "dist").mkdir()  # empty dist/ — no files

    checker = ExitCriteriaChecker()
    summary = _make_default_summary()
    summary["hasBuildFailure"] = False  # npm build claims success

    result = checker.evaluate_from_summary(summary, output_dir)

    # dist/ exists but is empty → fatal
    assert result["isComplete"] is False


def test_multiple_fatal_failures_reported(tmp_path: Path) -> None:
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()

    checker = ExitCriteriaChecker()
    summary = _make_default_summary()
    summary["tokensParseable"] = False  # Fatal 1
    summary["wcagContrastPassed"] = False  # Fatal 5

    result = checker.evaluate_from_summary(summary, output_dir)

    assert result["isComplete"] is False
    failed = [c for c in result["criteria"] if c["status"] == "failed"]
    assert len(failed) >= 2


# ---------------------------------------------------------------------------
# write_to_summary
# ---------------------------------------------------------------------------


def test_write_to_summary_writes_exit_criteria_section(tmp_path: Path) -> None:
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()
    (output_dir / "dist").mkdir()
    write_file(output_dir, "dist/index.js", "built")
    reports = output_dir / "reports"
    reports.mkdir()

    checker = ExitCriteriaChecker()
    summary = _make_default_summary()
    exit_result = checker.evaluate_from_summary(summary, output_dir)
    checker.write_to_summary(output_dir, exit_result)

    data = json.loads((reports / "generation-summary.json").read_text())
    assert "exitCriteria" in data
    assert data["exitCriteria"]["isComplete"] is True


def test_write_to_summary_preserves_existing_keys(tmp_path: Path) -> None:
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()
    (output_dir / "dist").mkdir()
    write_file(output_dir, "dist/index.js", "built")
    reports = output_dir / "reports"
    reports.mkdir()
    existing = {"phase3": {"components": [{"name": "Button"}]}}
    (reports / "generation-summary.json").write_text(json.dumps(existing))

    checker = ExitCriteriaChecker()
    summary = _make_default_summary()
    exit_result = checker.evaluate_from_summary(summary, output_dir)
    checker.write_to_summary(output_dir, exit_result)

    data = json.loads((reports / "generation-summary.json").read_text())
    assert data["phase3"]["components"][0]["name"] == "Button"
    assert "exitCriteria" in data


def test_warning_count_is_zero_when_all_warnings_pass(tmp_path: Path) -> None:
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()
    (output_dir / "dist").mkdir()
    write_file(output_dir, "dist/index.js", "/* built */")

    checker = ExitCriteriaChecker()
    result = checker.evaluate_from_summary(_make_default_summary(), output_dir)

    assert result["warningCount"] == 0
