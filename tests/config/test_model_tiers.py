"""Task 1.2 — model tier configuration tests."""

import pytest

from daf.config.model_tiers import (
    TIER1_DEFAULT,
    TIER2_DEFAULT,
    TIER3_DEFAULT,
    load_model_tiers,
)


def test_defaults_when_no_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DAF_TIER1_MODEL", raising=False)
    monkeypatch.delenv("DAF_TIER2_MODEL", raising=False)
    monkeypatch.delenv("DAF_TIER3_MODEL", raising=False)

    tiers = load_model_tiers()

    assert tiers.tier1 == TIER1_DEFAULT
    assert tiers.tier2 == TIER2_DEFAULT
    assert tiers.tier3 == TIER3_DEFAULT


def test_env_var_overrides_tier1(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DAF_TIER1_MODEL", "claude-opus-4-20250514")
    tiers = load_model_tiers()
    assert tiers.tier1 == "claude-opus-4-20250514"


def test_env_var_overrides_tier2(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DAF_TIER2_MODEL", "claude-opus-4-20250514")
    tiers = load_model_tiers()
    assert tiers.tier2 == "claude-opus-4-20250514"


def test_env_var_overrides_tier3(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DAF_TIER3_MODEL", "claude-sonnet-4-20250514")
    tiers = load_model_tiers()
    assert tiers.tier3 == "claude-sonnet-4-20250514"


def test_model_tiers_is_frozen() -> None:
    tiers = load_model_tiers()
    with pytest.raises((AttributeError, TypeError)):
        tiers.tier1 = "other"  # type: ignore[misc]


def test_tier1_and_tier2_defaults_are_equal() -> None:
    assert TIER1_DEFAULT == TIER2_DEFAULT


def test_tier3_default_differs_from_tier1() -> None:
    assert TIER3_DEFAULT != TIER1_DEFAULT
