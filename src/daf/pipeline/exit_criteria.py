"""Exit criteria enforcement (task 3.8).

Verifies all 15 exit criteria before marking the pipeline generation ``isComplete``.

Criterion list (per spec)
--------------------------
**Fatal (8) — ``isComplete: false`` if any fail:**

1.  Token JSON parses without error
2.  Token JSON conforms to W3C DTCG schema
3.  All semantic token references resolve to global tokens
4.  All component token references resolve to semantic tokens
5.  All foreground/background color pairs meet WCAG target
6.  CSS custom properties have no undefined references
7.  TypeScript compiles with zero errors
8.  ``npm install`` and ``npm run build`` succeed; ``dist/`` is non-empty

**Warning (7) — ``isComplete`` remains ``true``; surfaced in output review:**

9.  All unit tests pass
10. No hardcoded color/spacing values in source
11. All interactive components have ARIA roles
12. All components score ≥70/100 on quality gate
13. Spec ↔ code ↔ docs consistency check passes
14. Component registry JSON is valid and complete
15. No components are marked ``failed``

Usage
-----
::

    checker = ExitCriteriaChecker()
    exit_result = checker.evaluate_from_summary(generation_summary_dict, output_dir)
    checker.write_to_summary(output_dir, exit_result)
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class ExitCriteriaSeverity(str, Enum):
    FATAL = "fatal"
    WARNING = "warning"


class ExitCriteriaStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"


@dataclass
class CriteriaResult:
    """Outcome for a single exit criterion.

    Attributes
    ----------
    criterion_id: 1-based id matching the spec (1–15).
    description: Human-readable criterion label.
    severity: FATAL or WARNING.
    status: PASSED or FAILED.
    details: Optional failure explanation (None when passed).
    """

    criterion_id: int
    description: str
    severity: ExitCriteriaSeverity
    status: ExitCriteriaStatus
    details: Optional[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.criterion_id,
            "description": self.description,
            "severity": self.severity.value,
            "status": self.status.value,
            "details": self.details,
        }


class ExitCriteriaChecker:
    """Evaluate all 15 exit criteria from a generation summary dict.

    The checker reads data from the summary dict (populated by earlier agents)
    rather than re-running the checks itself — it is the enforcement layer, not
    the verification layer.  This keeps it deterministic and fast.
    """

    def evaluate_from_summary(
        self,
        summary: dict[str, Any],
        output_dir: Path,
    ) -> dict[str, Any]:
        """Evaluate all 15 criteria and return an exitCriteria dict.

        Parameters
        ----------
        summary:
            The accumulated generation summary dict (may be the full
            ``generation-summary.json`` or a subset).
        output_dir:
            Output directory path; used to check ``dist/`` for criterion 8.

        Returns
        -------
        dict with:
          ``criteria``:       list of per-criterion dicts (id, description, …)
          ``allFatalPassed``: bool — True only when all 8 fatal criteria pass
          ``warningCount``:   int — number of warning criteria that failed
          ``isComplete``:     bool — True when ``allFatalPassed`` is True
        """
        results: list[CriteriaResult] = [
            self._c1(summary),
            self._c2(summary),
            self._c3(summary),
            self._c4(summary),
            self._c5(summary),
            self._c6(summary),
            self._c7(summary),
            self._c8(summary, output_dir),
            self._c9(summary),
            self._c10(summary),
            self._c11(summary),
            self._c12(summary),
            self._c13(summary),
            self._c14(summary),
            self._c15(summary),
        ]

        all_fatal_passed = all(
            r.status == ExitCriteriaStatus.PASSED
            for r in results
            if r.severity == ExitCriteriaSeverity.FATAL
        )
        warning_count = sum(
            1
            for r in results
            if r.severity == ExitCriteriaSeverity.WARNING
            and r.status == ExitCriteriaStatus.FAILED
        )

        return {
            "criteria": [r.to_dict() for r in results],
            "allFatalPassed": all_fatal_passed,
            "warningCount": warning_count,
            "isComplete": all_fatal_passed,
        }

    def write_to_summary(
        self,
        output_dir: Path,
        exit_result: dict[str, Any],
    ) -> None:
        """Write *exit_result* into the ``exitCriteria`` key of generation-summary.json.

        Merges with any existing content; creates the file if absent.

        Parameters
        ----------
        output_dir:
            Absolute path to the pipeline output directory.
        exit_result:
            The dict returned by :meth:`evaluate_from_summary`.
        """
        reports_dir = output_dir / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        report_path = reports_dir / "generation-summary.json"

        existing: dict[str, Any] = {}
        if report_path.exists():
            try:
                existing = json.loads(report_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                existing = {}

        existing["exitCriteria"] = exit_result
        report_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")

    # ------------------------------------------------------------------
    # Individual criteria helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _pass(cid: int, desc: str, severity: ExitCriteriaSeverity) -> CriteriaResult:
        return CriteriaResult(cid, desc, severity, ExitCriteriaStatus.PASSED, None)

    @staticmethod
    def _fail(cid: int, desc: str, severity: ExitCriteriaSeverity, details: str) -> CriteriaResult:
        return CriteriaResult(cid, desc, severity, ExitCriteriaStatus.FAILED, details)

    def _c1(self, s: dict[str, Any]) -> CriteriaResult:
        desc = "Token JSON parses without error"
        ok = bool(s.get("tokensParseable", True))
        return self._pass(1, desc, ExitCriteriaSeverity.FATAL) if ok else self._fail(
            1, desc, ExitCriteriaSeverity.FATAL, "One or more token JSON files failed to parse."
        )

    def _c2(self, s: dict[str, Any]) -> CriteriaResult:
        desc = "Token JSON conforms to W3C DTCG schema"
        ok = bool(s.get("tokensDtcgValid", True))
        return self._pass(2, desc, ExitCriteriaSeverity.FATAL) if ok else self._fail(
            2, desc, ExitCriteriaSeverity.FATAL, "Token JSON does not conform to W3C DTCG schema."
        )

    def _c3(self, s: dict[str, Any]) -> CriteriaResult:
        desc = "All semantic token references resolve to global tokens"
        ok = bool(s.get("semanticRefsResolve", True))
        return self._pass(3, desc, ExitCriteriaSeverity.FATAL) if ok else self._fail(
            3, desc, ExitCriteriaSeverity.FATAL,
            "One or more semantic token references do not resolve to a global token.",
        )

    def _c4(self, s: dict[str, Any]) -> CriteriaResult:
        desc = "All component token references resolve to semantic tokens"
        ok = bool(s.get("componentRefsResolve", True))
        return self._pass(4, desc, ExitCriteriaSeverity.FATAL) if ok else self._fail(
            4, desc, ExitCriteriaSeverity.FATAL,
            "One or more component token references do not resolve to a semantic token.",
        )

    def _c5(self, s: dict[str, Any]) -> CriteriaResult:
        desc = "All foreground/background color pairs meet WCAG target"
        ok = bool(s.get("wcagContrastPassed", True))
        return self._pass(5, desc, ExitCriteriaSeverity.FATAL) if ok else self._fail(
            5, desc, ExitCriteriaSeverity.FATAL,
            "One or more color pairs fail the configured WCAG contrast target.",
        )

    def _c6(self, s: dict[str, Any]) -> CriteriaResult:
        desc = "CSS custom properties have no undefined references"
        has_undefined = bool(s.get("cssUndefinedRefs", False))
        return self._pass(6, desc, ExitCriteriaSeverity.FATAL) if not has_undefined else self._fail(
            6, desc, ExitCriteriaSeverity.FATAL,
            "CSS custom properties reference one or more undefined variables.",
        )

    def _c7(self, s: dict[str, Any]) -> CriteriaResult:
        desc = "TypeScript compiles with zero errors"
        errors = int(s.get("typescriptErrors", 0))
        return self._pass(7, desc, ExitCriteriaSeverity.FATAL) if errors == 0 else self._fail(
            7, desc, ExitCriteriaSeverity.FATAL, f"TypeScript compilation produced {errors} error(s)."
        )

    def _c8(self, s: dict[str, Any], output_dir: Path) -> CriteriaResult:
        desc = "npm install and npm run build succeed; dist/ is non-empty"
        build_failed = bool(s.get("hasBuildFailure", False))
        if build_failed:
            return self._fail(8, desc, ExitCriteriaSeverity.FATAL, "npm install or npm run build failed.")
        # Also verify dist/ exists and is non-empty
        dist_dir = output_dir / "dist"
        if not dist_dir.exists() or not any(dist_dir.iterdir()):
            return self._fail(
                8, desc, ExitCriteriaSeverity.FATAL,
                "dist/ is empty or does not exist after build."
            )
        return self._pass(8, desc, ExitCriteriaSeverity.FATAL)

    def _c9(self, s: dict[str, Any]) -> CriteriaResult:
        desc = "All unit tests pass"
        has_failures = bool(s.get("hasTestFailures", False))
        return self._pass(9, desc, ExitCriteriaSeverity.WARNING) if not has_failures else self._fail(
            9, desc, ExitCriteriaSeverity.WARNING,
            "One or more unit tests are failing (non-blocking).",
        )

    def _c10(self, s: dict[str, Any]) -> CriteriaResult:
        desc = "No hardcoded color/spacing values in source"
        detected = bool(s.get("hardcodedValuesDetected", False))
        return self._pass(10, desc, ExitCriteriaSeverity.WARNING) if not detected else self._fail(
            10, desc, ExitCriteriaSeverity.WARNING,
            "Hardcoded values detected in source (see reports/token-compliance.json).",
        )

    def _c11(self, s: dict[str, Any]) -> CriteriaResult:
        desc = "All interactive components have ARIA roles"
        missing = bool(s.get("interactiveComponentsMissingAria", False))
        return self._pass(11, desc, ExitCriteriaSeverity.WARNING) if not missing else self._fail(
            11, desc, ExitCriteriaSeverity.WARNING,
            "One or more interactive components are missing ARIA roles (see reports/a11y-audit.json).",
        )

    def _c12(self, s: dict[str, Any]) -> CriteriaResult:
        desc = "All components score ≥70/100 on quality gate"
        below = bool(s.get("qualityGateBelowThreshold", False))
        return self._pass(12, desc, ExitCriteriaSeverity.WARNING) if not below else self._fail(
            12, desc, ExitCriteriaSeverity.WARNING,
            "One or more components scored below 70/100 (see reports/quality-scorecard.json).",
        )

    def _c13(self, s: dict[str, Any]) -> CriteriaResult:
        desc = "Spec ↔ code ↔ docs consistency check passes"
        drift = bool(s.get("specCodeDocsDriftDetected", False))
        return self._pass(13, desc, ExitCriteriaSeverity.WARNING) if not drift else self._fail(
            13, desc, ExitCriteriaSeverity.WARNING,
            "Spec/code/docs drift detected (see reports/drift-report.json).",
        )

    def _c14(self, s: dict[str, Any]) -> CriteriaResult:
        desc = "Component registry JSON is valid and complete"
        incomplete = bool(s.get("registryIncomplete", False))
        return self._pass(14, desc, ExitCriteriaSeverity.WARNING) if not incomplete else self._fail(
            14, desc, ExitCriteriaSeverity.WARNING,
            "registry/components.json is missing entries or is invalid.",
        )

    def _c15(self, s: dict[str, Any]) -> CriteriaResult:
        desc = "No components are marked failed"
        failed = list(s.get("failedComponents", []))
        return self._pass(15, desc, ExitCriteriaSeverity.WARNING) if not failed else self._fail(
            15, desc, ExitCriteriaSeverity.WARNING,
            f"{len(failed)} component(s) exhausted retries and are marked failed: "
            + ", ".join(str(c) for c in failed[:5])
            + (" …" if len(failed) > 5 else ""),
        )
