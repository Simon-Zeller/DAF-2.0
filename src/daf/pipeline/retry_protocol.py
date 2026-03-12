"""Per-component retry protocol (task 3.3).

Implements the bounded 3-attempt retry loop used by Phase 1–3 generator/validator
pairs. Each retry attempt includes all prior rejection feedback appended to the
original task context.

Usage pattern
-------------
1. Create a ``RetryProtocol`` (default ``max_attempts=3``).
2. Create a ``ComponentRetryState`` per component at the start of generation.
3. After each failed validation, call ``protocol.record_rejection(state, rejection, last_output)``.
   - If attempts remain, ``status`` stays ``PENDING``.
   - If the maximum is reached, ``RetryExhaustedError`` is raised; ``state.status``
     is set to ``FAILED`` and ``state.last_best_attempt`` preserves the final output.
4. Call ``protocol.build_retry_context(state, original_task)`` to get the full
   prompt context for the next generator invocation.
5. On successful validation call ``state.mark_passed()``.

Retry boundaries (per spec)
---------------------------
- Token Foundation Agent ↔ Token Validation Agent
- Code Generation Agent ↔ Spec Validation Agent
- Code Generation Agent ↔ Render Validation Agent
- Code Generation Agent ↔ TypeScript Compiler
- Accessibility Agent ↔ axe-core
- Accessibility Agent ↔ TypeScript Compiler + Render Validation Agent
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

DEFAULT_MAX_ATTEMPTS = 3


class RetryStatus(str, Enum):
    """Lifecycle status of a component in the retry loop."""

    PENDING = "pending"
    """Generation/validation is still in progress (attempts remain)."""

    PASSED = "passed"
    """Component passed all validators; no further retry needed."""

    FAILED = "failed"
    """Component exhausted all retry attempts; marked failed in generation report."""


@dataclass
class StructuredRejection:
    """Structured output from a validator indicating why generation failed.

    Attributes
    ----------
    check_name:
        Machine-readable identifier for the failed check (e.g. ``"missing-props"``).
    error_details:
        Human-readable description of the exact error(s) found.
    suggested_fix:
        Specific, actionable suggestion for the generator to correct the output.
    """

    check_name: str
    error_details: str
    suggested_fix: str

    def __str__(self) -> str:
        return (
            f"[{self.check_name}] {self.error_details} — suggested fix: {self.suggested_fix}"
        )


@dataclass
class ComponentRetryState:
    """Mutable per-component state for the retry loop.

    Attributes
    ----------
    component_name:
        The name of the component being generated (e.g. ``"Button"``).
    status:
        Current lifecycle status (PENDING / PASSED / FAILED).
    attempt_count:
        Number of validation attempts recorded so far.
    rejections:
        All rejections received, in chronological order.
    last_best_attempt:
        The last generator output before exhaustion.  Preserved so the Rollback
        Agent can store it for post-run inspection.
    """

    component_name: str
    status: RetryStatus = RetryStatus.PENDING
    attempt_count: int = 0
    rejections: list[StructuredRejection] = field(default_factory=list)
    last_best_attempt: Optional[str] = None

    def record_rejection(self, rejection: StructuredRejection) -> None:
        """Append *rejection* and increment the attempt counter.

        This is an internal helper used only by ``RetryProtocol.record_rejection``.
        Direct callers should use ``RetryProtocol`` instead.
        """
        self.rejections.append(rejection)
        self.attempt_count += 1

    def mark_failed(self, last_best_attempt: str) -> None:
        """Mark this component as permanently failed after retry exhaustion."""
        self.status = RetryStatus.FAILED
        self.last_best_attempt = last_best_attempt

    def mark_passed(self) -> None:
        """Mark this component as successfully validated."""
        self.status = RetryStatus.PASSED


class RetryExhaustedError(RuntimeError):
    """Raised by ``RetryProtocol.record_rejection`` when max attempts are reached.

    The component state is updated to ``FAILED`` before this exception is raised.
    The pipeline should catch this, log the failure in the generation report, and
    continue with the next component — it MUST NOT re-raise or abort the pipeline.
    """

    def __init__(self, component_name: str, max_attempts: int) -> None:
        super().__init__(
            f"Component '{component_name}' exhausted {max_attempts} retry attempts "
            "and has been marked failed. The last best attempt has been preserved."
        )
        self.component_name = component_name
        self.max_attempts = max_attempts


class RetryProtocol:
    """Orchestrates the bounded retry loop for a single generator/validator pair.

    Parameters
    ----------
    max_attempts:
        Maximum number of validation attempts before a component is marked failed.
        Defaults to 3 (per spec).
    """

    def __init__(self, max_attempts: int = DEFAULT_MAX_ATTEMPTS) -> None:
        self.max_attempts = max_attempts

    def record_rejection(
        self,
        state: ComponentRetryState,
        rejection: StructuredRejection,
        last_output: str,
    ) -> None:
        """Record a validation failure and advance the retry state.

        If this rejection brings the attempt count to ``max_attempts``, the
        component is marked ``FAILED``, ``last_best_attempt`` is set to
        *last_output*, and ``RetryExhaustedError`` is raised.

        Parameters
        ----------
        state:
            The mutable state object for the component being retried.
        rejection:
            Structured rejection from the validator.
        last_output:
            The generator output produced in this attempt (preserved as
            ``last_best_attempt`` when exhaustion occurs).

        Raises
        ------
        RetryExhaustedError
            When the attempt count reaches ``max_attempts`` after recording
            this rejection.
        """
        state.record_rejection(rejection)

        if state.attempt_count >= self.max_attempts:
            state.mark_failed(last_best_attempt=last_output)
            raise RetryExhaustedError(state.component_name, self.max_attempts)

    def build_retry_context(
        self,
        state: ComponentRetryState,
        original_task: str,
    ) -> str:
        """Construct the full context string for the next generator invocation.

        Per spec: "Each retry attempt SHALL include all prior rejection feedback
        appended to the original task context."

        The returned string must be passed verbatim to the generator as its
        task prompt so it has the full rejection history.

        Parameters
        ----------
        state:
            The current retry state (with at least one recorded rejection).
        original_task:
            The original generation task description.

        Returns
        -------
        str
            A formatted context block combining the original task with all
            prior rejections in chronological order.
        """
        parts = [original_task]
        if state.rejections:
            parts.append("\n--- Prior validation rejections ---")
            for i, rejection in enumerate(state.rejections, start=1):
                parts.append(
                    f"\nAttempt {i} rejection:\n"
                    f"  Check: {rejection.check_name}\n"
                    f"  Error: {rejection.error_details}\n"
                    f"  Suggested fix: {rejection.suggested_fix}"
                )
        return "\n".join(parts)
