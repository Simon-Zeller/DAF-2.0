"""Tests for per-component retry protocol (task 3.3).

Covers:
  - StructuredRejection: stores check names, error details, suggested fix
  - ComponentRetryState: tracks attempt count and accumulated rejections
  - RetryProtocol: enforces 3-attempt max, accumulates context, marks failed
  - Context accumulation: all prior rejections included on each retry
  - Exhaust retry: component marked failed after 3 attempts
  - Last-best-attempt is preserved on exhaustion
"""

from __future__ import annotations

import pytest

from daf.pipeline.retry_protocol import (
    ComponentRetryState,
    RetryExhaustedError,
    RetryProtocol,
    RetryStatus,
    StructuredRejection,
)

MAX_ATTEMPTS = 3


# ---------------------------------------------------------------------------
# StructuredRejection
# ---------------------------------------------------------------------------


def test_structured_rejection_stores_all_fields() -> None:
    r = StructuredRejection(
        check_name="missing-props",
        error_details="Button is missing required prop 'variant'",
        suggested_fix="Add variant prop with type 'primary' | 'secondary'",
    )
    assert r.check_name == "missing-props"
    assert "variant" in r.error_details
    assert "variant prop" in r.suggested_fix


def test_structured_rejection_string_representation_includes_check_name() -> None:
    r = StructuredRejection(
        check_name="broken-token-ref",
        error_details="Token --color-bg-primary not found",
        suggested_fix="Use semantic token colorBgPrimary",
    )
    assert "broken-token-ref" in str(r)


# ---------------------------------------------------------------------------
# ComponentRetryState
# ---------------------------------------------------------------------------


def test_initial_state_is_pending() -> None:
    state = ComponentRetryState(component_name="Button")
    assert state.status == RetryStatus.PENDING
    assert state.attempt_count == 0
    assert state.rejections == []


def test_record_rejection_increments_attempt(tmp_path) -> None:
    state = ComponentRetryState(component_name="Input")
    rejection = StructuredRejection("type-error", "Type error in props", "Fix")
    state.record_rejection(rejection)
    assert state.attempt_count == 1
    assert len(state.rejections) == 1


def test_record_rejection_accumulates_all_rejections() -> None:
    state = ComponentRetryState(component_name="Modal")
    r1 = StructuredRejection("check-1", "Error 1", "Fix 1")
    r2 = StructuredRejection("check-2", "Error 2", "Fix 2")
    state.record_rejection(r1)
    state.record_rejection(r2)
    assert len(state.rejections) == 2
    assert state.rejections[0] is r1
    assert state.rejections[1] is r2


def test_mark_failed_sets_status() -> None:
    state = ComponentRetryState(component_name="Card")
    state.mark_failed(last_best_attempt="<TSX with partial impl>")
    assert state.status == RetryStatus.FAILED


def test_mark_failed_preserves_last_best_attempt() -> None:
    state = ComponentRetryState(component_name="Badge")
    state.mark_failed(last_best_attempt="<some TSX>")
    assert state.last_best_attempt == "<some TSX>"


def test_mark_passed_sets_status() -> None:
    state = ComponentRetryState(component_name="Alert")
    state.mark_passed()
    assert state.status == RetryStatus.PASSED


# ---------------------------------------------------------------------------
# RetryProtocol
# ---------------------------------------------------------------------------


def test_retry_protocol_allows_up_to_max_attempts() -> None:
    protocol = RetryProtocol(max_attempts=MAX_ATTEMPTS)
    state = ComponentRetryState(component_name="Button")

    # Record 2 rejections — should not raise
    protocol.record_rejection(
        state,
        StructuredRejection("check-1", "err", "fix"),
        last_output="output-1",
    )
    protocol.record_rejection(
        state,
        StructuredRejection("check-2", "err", "fix"),
        last_output="output-2",
    )
    assert state.attempt_count == 2
    assert state.status == RetryStatus.PENDING


def test_retry_protocol_raises_after_max_attempts() -> None:
    protocol = RetryProtocol(max_attempts=MAX_ATTEMPTS)
    state = ComponentRetryState(component_name="Select")

    for i in range(MAX_ATTEMPTS):
        if i < MAX_ATTEMPTS - 1:
            protocol.record_rejection(
                state,
                StructuredRejection(f"check-{i}", "err", "fix"),
                last_output=f"output-{i}",
            )
        else:
            with pytest.raises(RetryExhaustedError):
                protocol.record_rejection(
                    state,
                    StructuredRejection(f"check-{i}", "err", "fix"),
                    last_output=f"output-{i}",
                )


def test_retry_exhaustion_marks_component_failed() -> None:
    protocol = RetryProtocol(max_attempts=MAX_ATTEMPTS)
    state = ComponentRetryState(component_name="Checkbox")

    for i in range(MAX_ATTEMPTS):
        try:
            protocol.record_rejection(
                state,
                StructuredRejection(f"check-{i}", "err", "fix"),
                last_output=f"output-{i}",
            )
        except RetryExhaustedError:
            pass

    assert state.status == RetryStatus.FAILED


def test_retry_exhaustion_preserves_last_best_attempt() -> None:
    protocol = RetryProtocol(max_attempts=MAX_ATTEMPTS)
    state = ComponentRetryState(component_name="Radio")
    last = "final-output"

    for i in range(MAX_ATTEMPTS):
        try:
            protocol.record_rejection(
                state,
                StructuredRejection(f"check-{i}", "err", "fix"),
                last_output=last if i == MAX_ATTEMPTS - 1 else f"output-{i}",
            )
        except RetryExhaustedError:
            pass

    assert state.last_best_attempt == last


def test_build_retry_context_includes_all_prior_rejections() -> None:
    protocol = RetryProtocol(max_attempts=MAX_ATTEMPTS)
    state = ComponentRetryState(component_name="Table")

    r1 = StructuredRejection("check-1", "Error from attempt 1", "Fix 1")
    r2 = StructuredRejection("check-2", "Error from attempt 2", "Fix 2")
    protocol.record_rejection(state, r1, last_output="out-1")
    protocol.record_rejection(state, r2, last_output="out-2")

    context = protocol.build_retry_context(state, original_task="Generate Table component")

    assert "Generate Table component" in context
    assert "Error from attempt 1" in context
    assert "Error from attempt 2" in context


def test_build_retry_context_attempt_3_has_all_prior(tmp_path) -> None:
    """On attempt 3, context must include rejections from attempts 1 AND 2."""
    protocol = RetryProtocol(max_attempts=MAX_ATTEMPTS)
    state = ComponentRetryState(component_name="Dropdown")

    r1 = StructuredRejection("check-a", "Rejection attempt 1", "Fix A")
    r2 = StructuredRejection("check-b", "Rejection attempt 2", "Fix B")

    protocol.record_rejection(state, r1, last_output="out-1")
    protocol.record_rejection(state, r2, last_output="out-2")

    context = protocol.build_retry_context(state, original_task="Task: Generate Dropdown")

    assert "Rejection attempt 1" in context
    assert "Rejection attempt 2" in context
    assert "Task: Generate Dropdown" in context
