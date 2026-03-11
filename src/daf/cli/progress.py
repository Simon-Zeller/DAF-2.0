"""Real-time progress reporter.

Prints current phase, crew, agent, and retry information during pipeline
execution.  All output goes through a ``sink`` callable (default: ``print``)
so the reporter is fully testable without capturing stdout.

Usage::

    reporter = ProgressReporter()
    reporter.phase_start(phase=1, phase_name="DS Bootstrap Crew")
    reporter.agent_start(phase=1, crew="DS Bootstrap Crew", agent="Brand Discovery Agent")
    reporter.component_retry(component="Button", attempt=2, max_attempts=3)
    reporter.phase_complete(phase=1, phase_name="DS Bootstrap Crew",
                            artifacts=["tokens/global.tokens.json"], warnings=[])
"""

from __future__ import annotations

from typing import Callable, Sequence


class ProgressReporter:
    """Emits structured progress lines during pipeline execution.

    Parameters
    ----------
    sink:
        Callable that receives each output line (defaults to ``print``).
        Pass a ``list.append`` in tests to capture output without patching
        stdout.
    """

    def __init__(self, sink: Callable[[str], None] = print) -> None:
        self._sink = sink

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def phase_start(self, phase: int, phase_name: str) -> None:
        """Emit a phase-start line."""
        self._emit(f"▶ Phase {phase} — {phase_name}")

    def agent_start(self, phase: int, crew: str, agent: str) -> None:
        """Emit an agent-start line showing current crew and agent."""
        self._emit(f"  Phase {phase} / {crew} — {agent}")

    def component_retry(self, component: str, attempt: int, max_attempts: int) -> None:
        """Emit an inline retry notice for a failing component."""
        self._emit(f"  ↺ {component} — retry {attempt}/{max_attempts}")

    def component_failed(self, component: str, reason: str) -> None:
        """Emit an inline failure notice for a component that exhausted retries."""
        self._emit(f"  ✗ {component} failed: {reason}")

    def phase_complete(
        self,
        phase: int,
        phase_name: str,
        artifacts: Sequence[str],
        warnings: Sequence[str],
    ) -> None:
        """Emit a phase-completion summary with artifacts written and warnings."""
        self._emit(f"✓ Phase {phase} complete — {phase_name}")
        if artifacts:
            self._emit(f"  Artifacts: {', '.join(artifacts)}")
        else:
            self._emit("  Artifacts: (none)")
        if warnings:
            for w in warnings:
                self._emit(f"  ⚠ {w}")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _emit(self, line: str) -> None:
        self._sink(line)
