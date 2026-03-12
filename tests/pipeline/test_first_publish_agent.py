"""Tests for FirstPublishAgent (tasks 3.1, 3.4, 3.5, 3.6).

Covers:
  3.1 — Phase-sequential execution: phases advance only when current phase
         completes or is marked failed; Rollback Agent instantiated at start.
  3.4 — Cross-phase retry routing: Phase 2 failure re-invokes Phase 1 and
         re-runs Phase 2; respects 3-attempt limit; restores pre-Phase-1
         checkpoint before each cross-phase re-run.
  3.5 — Crew-level retry for Phases 4–6: entire crew retried up to 2 times;
         marked failed after exhaustion but pipeline continues.
  3.6 — Resume-on-failure: discovers most recent valid checkpoint, re-runs
         failed phase from scratch (no automatic retry of the failed phase).
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from daf.pipeline.first_publish_agent import (
    FirstPublishAgent,
    PhaseOutcome,
    PhaseResult,
    PhaseStatus,
    ResumeMode,
)


# ---------------------------------------------------------------------------
# Helpers: simple crew callables
# ---------------------------------------------------------------------------


def make_crew(status: PhaseStatus, attempts_until_pass: int = 1) -> Callable[..., PhaseResult]:
    """Return a crew callable that fails for *attempts_until_pass - 1* calls then passes."""
    call_count = [0]

    def crew(output_dir: Path) -> PhaseResult:
        call_count[0] += 1
        if call_count[0] >= attempts_until_pass:
            return PhaseResult(status=PhaseStatus.COMPLETE, outcome=PhaseOutcome.SUCCESS)
        return PhaseResult(status=PhaseStatus.FAILED, outcome=PhaseOutcome.VALIDATION_ERROR)

    return crew


def always_pass(output_dir: Path) -> PhaseResult:
    return PhaseResult(status=PhaseStatus.COMPLETE, outcome=PhaseOutcome.SUCCESS)


def always_fail(output_dir: Path) -> PhaseResult:
    return PhaseResult(status=PhaseStatus.FAILED, outcome=PhaseOutcome.VALIDATION_ERROR)


# ---------------------------------------------------------------------------
# 3.1 — Phase-sequential execution
# ---------------------------------------------------------------------------


def test_phases_run_in_order(tmp_path: Path) -> None:
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()

    order: list[int] = []

    def make_tracking_crew(phase: int) -> Callable[..., PhaseResult]:
        def crew(d: Path) -> PhaseResult:
            order.append(phase)
            return PhaseResult(status=PhaseStatus.COMPLETE, outcome=PhaseOutcome.SUCCESS)
        return crew

    agent = FirstPublishAgent(output_dir=output_dir)
    agent.run(
        phase_crews={
            1: make_tracking_crew(1),
            2: make_tracking_crew(2),
            3: make_tracking_crew(3),
        }
    )

    assert order == [1, 2, 3]


def test_failed_phase_does_not_advance(tmp_path: Path) -> None:
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()

    ran: list[int] = []

    def failing_crew(d: Path) -> PhaseResult:
        ran.append(1)
        return PhaseResult(status=PhaseStatus.FAILED, outcome=PhaseOutcome.VALIDATION_ERROR)

    def should_not_run(d: Path) -> PhaseResult:
        ran.append(2)
        return PhaseResult(status=PhaseStatus.COMPLETE, outcome=PhaseOutcome.SUCCESS)

    agent = FirstPublishAgent(output_dir=output_dir)
    result = agent.run(
        phase_crews={
            1: failing_crew,
            2: should_not_run,
        }
    )

    assert 2 not in ran
    assert result.final_phase_reached == 1


def test_rollback_agent_instantiated_before_phase_1(tmp_path: Path) -> None:
    """The Rollback Agent must write a pre-Phase-1 checkpoint (phase 0) before
    any crew runs."""
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()

    agent = FirstPublishAgent(output_dir=output_dir)
    agent.run(phase_crews={1: always_pass})

    # A phase-0 checkpoint should exist
    cp_meta = output_dir / ".daf-checkpoints" / "phase-0.json"
    assert cp_meta.exists()


def test_checkpoint_written_after_each_phase(tmp_path: Path) -> None:
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()

    agent = FirstPublishAgent(output_dir=output_dir)
    agent.run(phase_crews={1: always_pass, 2: always_pass})

    assert (output_dir / ".daf-checkpoints" / "phase-1.json").exists()
    assert (output_dir / ".daf-checkpoints" / "phase-2.json").exists()


def test_all_phases_complete_returns_success(tmp_path: Path) -> None:
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()

    agent = FirstPublishAgent(output_dir=output_dir)
    result = agent.run(phase_crews={1: always_pass, 2: always_pass, 3: always_pass})

    assert result.success is True
    assert result.final_phase_reached == 3


# ---------------------------------------------------------------------------
# 3.4 — Cross-phase retry routing
# ---------------------------------------------------------------------------


def test_cross_phase_retry_re_invokes_phase_1_on_phase_2_failure(tmp_path: Path) -> None:
    """When Phase 2 fails, Phase 1 should be re-invoked."""
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()

    phase1_runs = [0]
    phase2_runs = [0]

    def phase1_crew(d: Path) -> PhaseResult:
        phase1_runs[0] += 1
        return PhaseResult(status=PhaseStatus.COMPLETE, outcome=PhaseOutcome.SUCCESS)

    def phase2_eventually_passes(d: Path) -> PhaseResult:
        phase2_runs[0] += 1
        if phase2_runs[0] >= 2:
            return PhaseResult(status=PhaseStatus.COMPLETE, outcome=PhaseOutcome.SUCCESS)
        return PhaseResult(
            status=PhaseStatus.FAILED,
            outcome=PhaseOutcome.VALIDATION_ERROR,
            rejection_context="Token naming violation",
        )

    agent = FirstPublishAgent(output_dir=output_dir)
    result = agent.run(
        phase_crews={1: phase1_crew, 2: phase2_eventually_passes},
        cross_phase_retry_map={2: 1},  # Phase 2 failure → re-run Phase 1
    )

    assert phase1_runs[0] >= 2  # Phase 1 ran more than once
    assert result.success is True


def test_cross_phase_retry_restores_checkpoint_before_re_run(tmp_path: Path) -> None:
    """Before re-running Phase 1, a checkpoint restore must occur."""
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()

    restore_calls: list[int] = []
    original_run = FirstPublishAgent._restore_checkpoint_for_retry

    def patched_restore(self: FirstPublishAgent, phase: int) -> None:
        restore_calls.append(phase)

    FirstPublishAgent._restore_checkpoint_for_retry = patched_restore  # type: ignore[method-assign]

    try:
        phase2_runs = [0]

        def phase2_eventually_passes(d: Path) -> PhaseResult:
            phase2_runs[0] += 1
            if phase2_runs[0] >= 2:
                return PhaseResult(status=PhaseStatus.COMPLETE, outcome=PhaseOutcome.SUCCESS)
            return PhaseResult(
                status=PhaseStatus.FAILED,
                outcome=PhaseOutcome.VALIDATION_ERROR,
                rejection_context="Token naming violation",
            )

        agent = FirstPublishAgent(output_dir=output_dir)
        agent.run(
            phase_crews={1: always_pass, 2: phase2_eventually_passes},
            cross_phase_retry_map={2: 1},
        )

        assert len(restore_calls) >= 1
    finally:
        FirstPublishAgent._restore_checkpoint_for_retry = original_run  # type: ignore[method-assign]


def test_cross_phase_retry_respects_3_attempt_limit(tmp_path: Path) -> None:
    """Cross-phase retry must stop after 3 total attempts."""
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()

    phase2_runs = [0]

    def always_fail_phase2(d: Path) -> PhaseResult:
        phase2_runs[0] += 1
        return PhaseResult(status=PhaseStatus.FAILED, outcome=PhaseOutcome.VALIDATION_ERROR)

    agent = FirstPublishAgent(output_dir=output_dir)
    result = agent.run(
        phase_crews={1: always_pass, 2: always_fail_phase2},
        cross_phase_retry_map={2: 1},
    )

    # Phase 2 should run at most 3 times total (including first attempt)
    assert phase2_runs[0] <= 3
    assert result.success is False


# ---------------------------------------------------------------------------
# 3.5 — Phase 4–6 crew-level retry
# ---------------------------------------------------------------------------


def test_phase_456_retries_entire_crew_on_failure(tmp_path: Path) -> None:
    """Phase 4–6 crews are retried up to 2 attempts on failure."""
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()

    phase4_runs = [0]

    def phase4_eventual_pass(d: Path) -> PhaseResult:
        phase4_runs[0] += 1
        if phase4_runs[0] >= 2:
            return PhaseResult(status=PhaseStatus.COMPLETE, outcome=PhaseOutcome.SUCCESS)
        return PhaseResult(status=PhaseStatus.FAILED, outcome=PhaseOutcome.CREW_ERROR)

    agent = FirstPublishAgent(output_dir=output_dir)
    result = agent.run(
        phase_crews={4: phase4_eventual_pass},
        crew_retry_phases={4, 5, 6},
    )

    assert phase4_runs[0] == 2
    assert result.success is True


def test_phase_456_marks_failed_after_2_retries_but_continues(tmp_path: Path) -> None:
    """After 2 failures of a Phase 4–6 crew, mark it failed but do not abort."""
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()

    phase5_runs = [0]
    phase6_runs = [0]

    def always_fail_phase5(d: Path) -> PhaseResult:
        phase5_runs[0] += 1
        return PhaseResult(status=PhaseStatus.FAILED, outcome=PhaseOutcome.CREW_ERROR)

    def phase6_pass(d: Path) -> PhaseResult:
        phase6_runs[0] += 1
        return PhaseResult(status=PhaseStatus.COMPLETE, outcome=PhaseOutcome.SUCCESS)

    agent = FirstPublishAgent(output_dir=output_dir)
    result = agent.run(
        phase_crews={5: always_fail_phase5, 6: phase6_pass},
        crew_retry_phases={5, 6},
    )

    # Phase 5 exhausted, Phase 6 still ran
    assert phase5_runs[0] == 2  # 2 attempts max for phase 4-6
    assert phase6_runs[0] == 1
    # Phase 5 failure is non-fatal
    assert 5 in result.failed_crews
    assert result.success is True  # pipeline completes since remaining phases pass


def test_phase_456_failure_recorded_in_pipeline_result(tmp_path: Path) -> None:
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()

    agent = FirstPublishAgent(output_dir=output_dir)
    result = agent.run(
        phase_crews={4: always_fail, 5: always_pass},
        crew_retry_phases={4, 5},
    )

    assert 4 in result.failed_crews


# ---------------------------------------------------------------------------
# 3.6 — Resume-on-failure
# ---------------------------------------------------------------------------


def test_resume_discovers_most_recent_checkpoint(tmp_path: Path) -> None:
    """Resume mode must start from the phase after the most recent checkpoint."""
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()

    # Simulate phases 1 and 2 already done: create their checkpoints
    from daf.pipeline.rollback_agent import RollbackAgent
    rb = RollbackAgent()
    rb.write_checkpoint(output_dir, phase=0)
    rb.write_checkpoint(output_dir, phase=1)
    rb.write_checkpoint(output_dir, phase=2)

    ran_phases: list[int] = []

    def tracking_crew(phase: int) -> Callable[..., PhaseResult]:
        def crew(d: Path) -> PhaseResult:
            ran_phases.append(phase)
            return PhaseResult(status=PhaseStatus.COMPLETE, outcome=PhaseOutcome.SUCCESS)
        return crew

    agent = FirstPublishAgent(output_dir=output_dir)
    agent.run(
        phase_crews={1: tracking_crew(1), 2: tracking_crew(2), 3: tracking_crew(3)},
        mode=ResumeMode.RESUME,
    )

    # Only Phase 3 should have run (Phases 1 and 2 had valid checkpoints)
    assert ran_phases == [3]


def test_resume_reruns_failed_phase_from_scratch(tmp_path: Path) -> None:
    """On resume, the failed phase re-runs fully (no partial resume of the phase)."""
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()

    from daf.pipeline.rollback_agent import RollbackAgent
    rb = RollbackAgent()
    rb.write_checkpoint(output_dir, phase=0)
    rb.write_checkpoint(output_dir, phase=1)
    # Phase 2 checkpoint missing — simulates Phase 2 failure mid-run

    ran_phases: list[int] = []

    def phase2_crew(d: Path) -> PhaseResult:
        ran_phases.append(2)
        return PhaseResult(status=PhaseStatus.COMPLETE, outcome=PhaseOutcome.SUCCESS)

    agent = FirstPublishAgent(output_dir=output_dir)
    agent.run(
        phase_crews={1: always_pass, 2: phase2_crew},
        mode=ResumeMode.RESUME,
    )

    assert 2 in ran_phases


def test_resume_no_checkpoint_runs_from_phase_1(tmp_path: Path) -> None:
    """With no checkpoint, resume falls back to running from Phase 1."""
    output_dir = tmp_path / "my-ds"
    output_dir.mkdir()

    ran_phases: list[int] = []

    def crew(phase: int) -> Callable[..., PhaseResult]:
        def run(d: Path) -> PhaseResult:
            ran_phases.append(phase)
            return PhaseResult(status=PhaseStatus.COMPLETE, outcome=PhaseOutcome.SUCCESS)
        return run

    agent = FirstPublishAgent(output_dir=output_dir)
    agent.run(
        phase_crews={1: crew(1), 2: crew(2)},
        mode=ResumeMode.RESUME,
    )

    assert ran_phases == [1, 2]
