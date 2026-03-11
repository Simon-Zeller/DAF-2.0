"""Task 1.3 — plugin registry tests."""

import json
from pathlib import Path

import pytest

from daf.plugins.registry import (
    PluginNotRegisteredError,
    PluginRegistry,
)


def test_register_and_get_returns_implementation() -> None:
    reg = PluginRegistry()
    sentinel = object()
    reg.register("my-tool", sentinel)
    assert reg.get("my-tool") is sentinel


def test_get_unknown_raises_plugin_not_registered_error() -> None:
    reg = PluginRegistry()
    with pytest.raises(PluginNotRegisteredError, match="unknown-tool"):
        reg.get("unknown-tool")


def test_register_overwrites_previous() -> None:
    reg = PluginRegistry()
    reg.register("tool", "v1")
    reg.register("tool", "v2")
    assert reg.get("tool") == "v2"


def test_registered_ids_sorted(tmp_path: Path) -> None:
    reg = PluginRegistry()
    reg.register("z-tool", None)
    reg.register("a-tool", None)
    assert reg.registered_ids == ["a-tool", "z-tool"]


def test_validate_against_config_passes_when_all_registered(tmp_path: Path) -> None:
    config = tmp_path / "pipeline-config.json"
    config.write_text(json.dumps({"plugins": {"required": ["compiler", "linter"]}}))

    reg = PluginRegistry()
    reg.register("compiler", object())
    reg.register("linter", object())

    reg.validate_against_config(config)  # must not raise


def test_validate_against_config_fails_for_missing_plugin(tmp_path: Path) -> None:
    config = tmp_path / "pipeline-config.json"
    config.write_text(json.dumps({"plugins": {"required": ["compiler", "missing-tool"]}}))

    reg = PluginRegistry()
    reg.register("compiler", object())

    with pytest.raises(PluginNotRegisteredError, match="missing-tool"):
        reg.validate_against_config(config)


def test_validate_against_config_passes_when_no_required_plugins(tmp_path: Path) -> None:
    config = tmp_path / "pipeline-config.json"
    config.write_text(json.dumps({}))

    reg = PluginRegistry()
    reg.validate_against_config(config)  # must not raise


def test_validate_against_config_raises_file_not_found() -> None:
    reg = PluginRegistry()
    with pytest.raises(FileNotFoundError):
        reg.validate_against_config(Path("/nonexistent/pipeline-config.json"))
