"""Pipeline Completeness Agent (Agent 34, Tier 3) — task 3.7.

Compares the output folder against the expected artifact list defined in PRD §2.3.
Lists missing or empty files and writes findings to the ``completeness`` section of
``reports/generation-summary.json``.

This agent is non-fatal: it always returns a result dict. The exit criteria
enforcer (task 3.8) uses the result to evaluate exit criterion 14 (component
registry valid and complete) and to populate warnings.

Expected artifact list
-----------------------
Covers all static-path required files from the PRD §2.3 output structure.
Dynamic component/primitive paths (``src/components/<Name>/…``) are not checked
here because their names depend on brand profile choices — their presence is
verified via the generation report created by the Design-to-Code Crew.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Required static artifacts (relative paths from output root)
# Must be present AND non-empty after a full successful run.
# ---------------------------------------------------------------------------

_REQUIRED_FILES: list[str] = [
    # Project scaffolding
    "package.json",
    "tsconfig.json",
    "vitest.config.ts",
    "vite.config.ts",
    "pipeline-config.json",
    "brand-profile.json",
    # Token tier files
    "tokens/global.tokens.json",
    "tokens/semantic.tokens.json",
    "tokens/component.tokens.json",
    "tokens/diff.json",
    # Compiled token outputs
    "tokens/compiled/variables.css",
    "tokens/compiled/variables-light.css",
    "tokens/compiled/variables-dark.css",
    "tokens/compiled/variables-high-contrast.css",
    "tokens/compiled/variables.scss",
    "tokens/compiled/tokens.ts",
    "tokens/compiled/tokens.json",
    # Source barrel exports
    "src/index.ts",
    "src/primitives/index.ts",
    "src/components/index.ts",
    # Documentation
    "docs/README.md",
    "docs/tokens.md",
    "docs/changelog.md",
    "docs/search-index.json",
    "docs/templates/rfc-template.md",
    "docs/decisions/generation-narrative.md",
    "docs/decisions/ADR-001-archetype-selection.md",
    "docs/decisions/ADR-002-token-scale-rationale.md",
    "docs/decisions/ADR-003-component-scope.md",
    # Governance
    "governance/ownership.json",
    "governance/quality-gates.json",
    "governance/deprecation-policy.json",
    "governance/workflow.json",
    "governance/rfc-process.md",
    # Registry
    "registry/components.json",
    "registry/tokens.json",
    "registry/composition-rules.json",
    "registry/compliance-rules.json",
    # Reports
    "reports/generation-summary.json",
    "reports/quality-scorecard.json",
    "reports/a11y-audit.json",
    "reports/token-compliance.json",
    "reports/composition-audit.json",
    "reports/drift-report.json",
    "reports/token-integrity.json",
    # Test scaffolds
    "tests/tokens.test.ts",
    "tests/a11y.test.ts",
    "tests/composition.test.ts",
    "tests/compliance.test.ts",
    # AI context files
    ".cursorrules",
    "copilot-instructions.md",
    "ai-context.json",
]


class PipelineCompletenessAgent:
    """Verify that all expected pipeline output artifacts are present and non-empty.

    Usage
    -----
    ::

        agent = PipelineCompletenessAgent()
        result = agent.check_completeness(output_dir)
        agent.write_to_summary(output_dir, result)
    """

    REQUIRED_FILES: list[str] = _REQUIRED_FILES

    def check_completeness(self, output_dir: Path) -> dict[str, list[str]]:
        """Compare *output_dir* against the expected artifact list.

        Parameters
        ----------
        output_dir:
            Absolute path to the pipeline output directory.

        Returns
        -------
        dict with keys:
          ``missing``: relative paths of files that do not exist.
          ``empty``:   relative paths of files that exist but contain no bytes.
        """
        missing: list[str] = []
        empty: list[str] = []

        for rel_str in self.REQUIRED_FILES:
            path = output_dir / rel_str
            if not path.exists():
                missing.append(rel_str)
            elif path.stat().st_size == 0:
                empty.append(rel_str)

        return {"missing": missing, "empty": empty}

    def write_to_summary(
        self,
        output_dir: Path,
        completeness: dict[str, list[str]],
    ) -> None:
        """Merge *completeness* result into ``reports/generation-summary.json``.

        Creates the report file if it does not exist.  Preserves all existing
        top-level keys — only the ``completeness`` key is written/overwritten.

        Parameters
        ----------
        output_dir:
            Absolute path to the pipeline output directory.
        completeness:
            The dict returned by :meth:`check_completeness`.
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

        existing["completeness"] = completeness
        report_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
