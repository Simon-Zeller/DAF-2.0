"""Tests for interview session persistence (task 2.10)."""

from __future__ import annotations

import json
from pathlib import Path

from daf.cli.session import (
    SESSION_FILE,
    InterviewSession,
    SessionState,
    discover_session,
    load_session,
)


# ---------------------------------------------------------------------------
# Fixtures helpers
# ---------------------------------------------------------------------------


def _full_answers() -> list[str | None]:
    """Return 19 step answers (all non-None = full session)."""
    return [
        "Acme",          # 1 name
        "enterprise-b2b",  # 2 archetype
        "#0A2463",       # 3 primary
        "#FF6B35",       # 4 secondary
        "#6B7280",       # 5 neutral
        "Inter",         # 6 heading font
        "Inter",         # 7 body font
        "major-third",   # 8 font scale
        "8px",           # 9 spacing
        "standard",      # 10 scope
        "medium",        # 11 border-radius
        "5-step",        # 12 elevation
        "200ms",         # 13 duration
        "ease-in-out",   # 14 easing
        "sm:640px,md:768px",  # 15 breakpoints
        "AA",            # 16 accessibility
        "light,dark",    # 17 modes
        "light",         # 18 default
        "no",            # 19 multi-brand
    ]


# ---------------------------------------------------------------------------
# SESSION_FILE constant
# ---------------------------------------------------------------------------


def test_session_filename() -> None:
    assert SESSION_FILE == ".daf-session.json"


# ---------------------------------------------------------------------------
# discover_session
# ---------------------------------------------------------------------------


def test_discover_no_session_file(tmp_path: Path) -> None:
    result = discover_session(tmp_path)
    assert result == SessionState.NOT_FOUND


def test_discover_valid_session(tmp_path: Path) -> None:
    answers: list[str | None] = [None] * 19
    answers[0] = "Acme"
    answers[1] = "enterprise-b2b"
    answers[2] = "#0A2463"
    session = InterviewSession(answers=answers, last_step=3)
    session.save(tmp_path)
    result = discover_session(tmp_path)
    assert result == SessionState.FOUND


def test_discover_corrupt_session(tmp_path: Path) -> None:
    (tmp_path / SESSION_FILE).write_text("not-json", encoding="utf-8")
    result = discover_session(tmp_path)
    assert result == SessionState.CORRUPT


def test_discover_missing_keys_session(tmp_path: Path) -> None:
    (tmp_path / SESSION_FILE).write_text(
        json.dumps({"answers": []}), encoding="utf-8"
    )
    result = discover_session(tmp_path)
    assert result == SessionState.CORRUPT


# ---------------------------------------------------------------------------
# load_session
# ---------------------------------------------------------------------------


def test_load_session_returns_interview_session(tmp_path: Path) -> None:
    session = InterviewSession(answers=[None] * 19, last_step=3)
    session.answers[0] = "Acme"  # type: ignore[index]
    session.save(tmp_path)
    loaded = load_session(tmp_path)
    assert loaded is not None
    assert loaded.last_step == 3
    assert loaded.answers[0] == "Acme"


def test_load_session_returns_none_when_not_found(tmp_path: Path) -> None:
    assert load_session(tmp_path) is None


def test_load_session_returns_none_when_corrupt(tmp_path: Path) -> None:
    (tmp_path / SESSION_FILE).write_text("{bad json", encoding="utf-8")
    assert load_session(tmp_path) is None


# ---------------------------------------------------------------------------
# InterviewSession.save and round-trip
# ---------------------------------------------------------------------------


def test_session_save_creates_file(tmp_path: Path) -> None:
    session = InterviewSession(answers=[None] * 19, last_step=0)
    session.save(tmp_path)
    assert (tmp_path / SESSION_FILE).exists()


def test_session_round_trip(tmp_path: Path) -> None:
    answers: list[str | None] = [None] * 19
    answers[0] = "Acme"
    answers[5] = "Inter"
    session = InterviewSession(answers=answers, last_step=6)
    session.save(tmp_path)
    loaded = load_session(tmp_path)
    assert loaded is not None
    assert loaded.answers[0] == "Acme"
    assert loaded.answers[5] == "Inter"
    assert loaded.last_step == 6


def test_session_full_answers_round_trip(tmp_path: Path) -> None:
    raw = _full_answers()
    session = InterviewSession(answers=raw, last_step=19)  # type: ignore[arg-type]
    session.save(tmp_path)
    loaded = load_session(tmp_path)
    assert loaded is not None
    assert loaded.answers == raw
    assert loaded.last_step == 19


# ---------------------------------------------------------------------------
# InterviewSession.delete
# ---------------------------------------------------------------------------


def test_session_delete_removes_file(tmp_path: Path) -> None:
    session = InterviewSession(answers=[None] * 19, last_step=0)
    session.save(tmp_path)
    InterviewSession.delete(tmp_path)
    assert not (tmp_path / SESSION_FILE).exists()


def test_session_delete_no_op_when_file_absent(tmp_path: Path) -> None:
    InterviewSession.delete(tmp_path)  # must not raise
    assert not (tmp_path / SESSION_FILE).exists()


# ---------------------------------------------------------------------------
# next_step property
# ---------------------------------------------------------------------------


def test_next_step_is_last_step_plus_one() -> None:
    session = InterviewSession(answers=[None] * 19, last_step=5)
    assert session.next_step == 6


def test_next_step_zero_when_no_steps_done() -> None:
    session = InterviewSession(answers=[None] * 19, last_step=0)
    assert session.next_step == 1
