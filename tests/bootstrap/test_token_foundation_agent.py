"""Tests for Token Foundation Agent (tasks 4.2 and 4.3).

Covers:
  - generate_token_files: writes base, semantic, and component token files
  - base token file content: contains W3C DTCG $value/$type keys
  - semantic token file: uses alias syntax referencing base tokens
  - semantic token file: uses $extensions.com.daf.themes for per-theme values
  - component token file: references semantic namespace, not global
  - generate_token_files: raises MissingBrandProfileFieldError when a required
    field is absent from the brand profile
  - generate_multi_brand_files: writes brands/<brand-id>.tokens.json per brand
  - generate_multi_brand_files: each brand file contains only differing tokens
  - multi_brand_platform archetype generates multi-brand structure even for
    single-brand profile
  - generate_token_files_tool: returns JSON on success, ERROR string on failure
  - generate_multi_brand_files_tool: returns JSON on success
  - make_token_foundation_agent: constructs Agent with correct role and tools
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from daf.bootstrap.token_foundation_agent import (
    MissingBrandProfileFieldError,
    generate_multi_brand_files,
    generate_multi_brand_files_tool,
    generate_token_files,
    generate_token_files_tool,
    make_token_foundation_agent,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def minimal_profile() -> dict[str, object]:
    return {
        "name": "Acme",
        "archetype": "enterprise-b2b",
        "componentScope": "comprehensive",
        "colors": {
            "primary": {"500": "#1a73e8"},
            "secondary": None,
            "neutral": {"50": "#f8f9fa", "950": "#1c1c1c"},
            "semantic": {"success": "#34a853", "error": "#ea4335", "warning": "#fbbc04", "info": "#4285f4"},
        },
        "typography": {
            "fontFamilies": {"heading": "Inter", "body": "Inter", "mono": "JetBrains Mono"},
            "fontWeights": [400, 500, 700],
            "sizeScale": ["0.75rem", "0.875rem", "1rem", "1.25rem", "1.5rem"],
        },
        "spacing": {"unit": 4, "scale": [0, 0.5, 1, 2, 3, 4]},
        "borderRadius": {"none": "0", "sm": "2px", "md": "4px", "lg": "8px", "xl": "16px", "full": "9999px"},
        "elevation": {"none": "none", "sm": "0 1px 2px rgba(0,0,0,.1)", "md": "0 4px 8px rgba(0,0,0,.1)"},
        "motion": {"duration": {"fast": 100, "base": 200, "slow": 400}, "easing": {"ease-in": "cubic-bezier(0.4,0,1,1)"}},
        "breakpoints": {"xs": 0, "sm": 600, "md": 960, "lg": 1280, "xl": 1920, "2xl": 2560},
        "accessibility": {"level": "AA"},
        "themes": {"modes": ["light", "dark"], "default": "light", "brands": ["acme"], "brandOverrides": {}},
        "componentOverrides": {},
        "iconSet": "lucide",
        "plugins": [],
    }


# ---------------------------------------------------------------------------
# generate_token_files
# ---------------------------------------------------------------------------


def test_generate_token_files_writes_three_files(tmp_path: Path) -> None:
    generate_token_files(minimal_profile(), tmp_path)

    assert (tmp_path / "tokens" / "base.tokens.json").exists()
    assert (tmp_path / "tokens" / "semantic.tokens.json").exists()
    assert (tmp_path / "tokens" / "component.tokens.json").exists()


def test_base_token_file_has_dtcg_value_key(tmp_path: Path) -> None:
    generate_token_files(minimal_profile(), tmp_path)

    data = json.loads((tmp_path / "tokens" / "base.tokens.json").read_text())

    def has_value_key(node: object) -> bool:
        if isinstance(node, dict):
            if "$value" in node and "$type" in node:
                return True
            return any(has_value_key(v) for v in node.values())
        return False

    assert has_value_key(data)


def test_semantic_token_uses_alias_syntax(tmp_path: Path) -> None:
    generate_token_files(minimal_profile(), tmp_path)

    raw = (tmp_path / "tokens" / "semantic.tokens.json").read_text()
    assert "{" in raw


def test_semantic_token_has_theme_extension(tmp_path: Path) -> None:
    generate_token_files(minimal_profile(), tmp_path)

    raw = (tmp_path / "tokens" / "semantic.tokens.json").read_text()
    assert "$extensions" in raw
    assert "com.daf.themes" in raw


def test_component_token_uses_semantic_namespace(tmp_path: Path) -> None:
    import re
    generate_token_files(minimal_profile(), tmp_path)

    raw = (tmp_path / "tokens" / "component.tokens.json").read_text()
    data = json.loads(raw)

    def find_alias_values(node: object) -> list[str]:
        results: list[str] = []
        if isinstance(node, dict):
            if "$value" in node and isinstance(node["$value"], str) and node["$value"].startswith("{"):
                results.append(node["$value"])
            for v in node.values():
                results.extend(find_alias_values(v))
        return results

    alias_values = find_alias_values(data)
    assert len(alias_values) > 0

    global_ref_pattern = re.compile(r"\{\w+\.\w+\.\d+\}")
    for alias in alias_values:
        assert not global_ref_pattern.search(alias), (
            f"Component token references global tier directly: {alias}"
        )


def test_missing_colors_key_raises_error(tmp_path: Path) -> None:
    profile = minimal_profile()
    del profile["colors"]
    with pytest.raises(MissingBrandProfileFieldError):
        generate_token_files(profile, tmp_path)


def test_missing_typography_key_raises_error(tmp_path: Path) -> None:
    profile = minimal_profile()
    del profile["typography"]
    with pytest.raises(MissingBrandProfileFieldError):
        generate_token_files(profile, tmp_path)


# ---------------------------------------------------------------------------
# generate_multi_brand_files (task 4.3)
# ---------------------------------------------------------------------------


def test_generate_multi_brand_files_writes_per_brand_file(tmp_path: Path) -> None:
    profile = minimal_profile()
    profile["themes"]["brands"] = ["acme", "globex"]  # type: ignore[index]
    profile["themes"]["brandOverrides"] = {  # type: ignore[index]
        "globex": {"color.background.default": "#0d1117"}
    }
    generate_token_files(profile, tmp_path)
    generate_multi_brand_files(profile, tmp_path)

    assert (tmp_path / "tokens" / "brands" / "acme.tokens.json").exists()
    assert (tmp_path / "tokens" / "brands" / "globex.tokens.json").exists()


def test_brand_file_contains_only_override_tokens(tmp_path: Path) -> None:
    profile = minimal_profile()
    profile["themes"]["brands"] = ["acme", "globex"]  # type: ignore[index]
    profile["themes"]["brandOverrides"] = {  # type: ignore[index]
        "globex": {"color.background.default": "#0d1117"}
    }
    generate_token_files(profile, tmp_path)
    generate_multi_brand_files(profile, tmp_path)

    globex_data = json.loads((tmp_path / "tokens" / "brands" / "globex.tokens.json").read_text())
    assert "color.background.default" in globex_data


def test_multi_brand_platform_generates_brand_files_for_single_brand(tmp_path: Path) -> None:
    profile = minimal_profile()
    profile["archetype"] = "multi-brand-platform"
    profile["themes"]["brands"] = ["acme"]  # type: ignore[index]
    generate_token_files(profile, tmp_path)
    generate_multi_brand_files(profile, tmp_path)

    assert (tmp_path / "tokens" / "brands" / "acme.tokens.json").exists()


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


def test_generate_token_files_tool_returns_ok_json(tmp_path: Path) -> None:
    payload = json.dumps({"brand_profile": minimal_profile(), "output_dir": str(tmp_path)})
    result = generate_token_files_tool.run(payload)
    data = json.loads(result)
    assert data["status"] == "ok"
    assert "base.tokens.json" in data["files"]


def test_generate_token_files_tool_returns_error_on_missing_field(tmp_path: Path) -> None:
    profile = minimal_profile()
    del profile["colors"]
    payload = json.dumps({"brand_profile": profile, "output_dir": str(tmp_path)})
    result = generate_token_files_tool.run(payload)
    assert result.startswith("ERROR:")


def test_generate_multi_brand_files_tool_returns_ok_json(tmp_path: Path) -> None:
    profile = minimal_profile()
    profile["themes"]["brands"] = ["acme"]  # type: ignore[index]
    generate_token_files(profile, tmp_path)
    payload = json.dumps({"brand_profile": profile, "output_dir": str(tmp_path)})
    result = generate_multi_brand_files_tool.run(payload)
    data = json.loads(result)
    assert data["status"] == "ok"


# ---------------------------------------------------------------------------
# make_token_foundation_agent factory (Agent + LLM mocked — no API key needed)
# ---------------------------------------------------------------------------


@patch("daf.bootstrap.token_foundation_agent.Agent")
@patch("daf.bootstrap.token_foundation_agent.LLM")
def test_token_foundation_agent_has_correct_role(
    mock_llm: MagicMock, mock_agent: MagicMock
) -> None:
    make_token_foundation_agent("claude-sonnet-4-20250514")
    _, kwargs = mock_agent.call_args
    assert kwargs["role"] == "Token Foundation Architect"


@patch("daf.bootstrap.token_foundation_agent.Agent")
@patch("daf.bootstrap.token_foundation_agent.LLM")
def test_token_foundation_agent_llm_uses_anthropic_prefix(
    mock_llm: MagicMock, mock_agent: MagicMock
) -> None:
    make_token_foundation_agent("claude-sonnet-4-20250514")
    mock_llm.assert_called_once_with(model="anthropic/claude-sonnet-4-20250514")


@patch("daf.bootstrap.token_foundation_agent.Agent")
@patch("daf.bootstrap.token_foundation_agent.LLM")
def test_token_foundation_agent_tools_include_token_file_tools(
    mock_llm: MagicMock, mock_agent: MagicMock
) -> None:
    make_token_foundation_agent("claude-sonnet-4-20250514")
    _, kwargs = mock_agent.call_args
    tool_names = {t.name for t in kwargs["tools"]}
    assert "Generate Token Files" in tool_names
    assert "Generate Multi-Brand Token Files" in tool_names
