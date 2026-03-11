"""Plugin registry.

Plugins are the abstraction layer between crews/agents and concrete tools
(token compilers, linters, TypeScript compiler wrappers, etc.).

Lifecycle
---------
1. At import time (or in pipeline startup), call ``registry.register(id, impl)``
   for every built-in plugin.
2. Before any phase runs, call ``registry.validate_against_config(path)`` to
   fail-fast if a plugin declared in ``pipeline-config.json`` has no registered
   implementation.
3. Agents call ``registry.get(id)`` to obtain the implementation and invoke it.

This ensures crews never reference compilers or linters directly and the
concrete tool can be swapped without touching pipeline core code.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class PluginNotRegisteredError(RuntimeError):
    """Raised when an agent requests a plugin that has not been registered."""


class PluginRegistry:
    """Central store for plugin implementations keyed by their config identifier."""

    def __init__(self) -> None:
        self._plugins: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, identifier: str, plugin: Any) -> None:
        """Register a plugin implementation under *identifier*.

        Overwrites any previously registered implementation for the same
        identifier (allows test doubles to replace built-ins).
        """
        self._plugins[identifier] = plugin

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def get(self, identifier: str) -> Any:
        """Return the registered plugin for *identifier*.

        Raises
        ------
        PluginNotRegisteredError
            If no plugin has been registered under *identifier*. The pipeline
            must not swallow this error — it indicates a missing registration
            that must be fixed before proceeding.
        """
        try:
            return self._plugins[identifier]
        except KeyError:
            raise PluginNotRegisteredError(
                f"Plugin '{identifier}' is not registered. "
                "Register an implementation via PluginRegistry.register() "
                "before starting the pipeline."
            ) from None

    # ------------------------------------------------------------------
    # Config validation (fail-fast at pipeline startup)
    # ------------------------------------------------------------------

    def validate_against_config(self, config_path: Path) -> None:
        """Fail-fast if any plugin declared in *pipeline-config.json* is absent.

        Reads the ``plugins.required`` list from the config file and asserts
        that every identifier has a registered implementation. Must be called
        once, before Phase 1 begins.

        Parameters
        ----------
        config_path:
            Absolute path to the output folder's ``pipeline-config.json``.

        Raises
        ------
        FileNotFoundError
            If *config_path* does not exist.
        PluginNotRegisteredError
            If one or more required plugins are not registered.
        """
        with config_path.open() as fh:
            config: dict[str, Any] = json.load(fh)

        required: list[str] = config.get("plugins", {}).get("required", [])
        missing = [pid for pid in required if pid not in self._plugins]

        if missing:
            raise PluginNotRegisteredError(
                f"Required plugin(s) not registered: {', '.join(missing)}. "
                "Ensure all plugins listed under 'plugins.required' in "
                "pipeline-config.json have implementations registered before "
                "pipeline start."
            )

    # ------------------------------------------------------------------
    # Introspection (for reporting / debug)
    # ------------------------------------------------------------------

    @property
    def registered_ids(self) -> list[str]:
        """Return a sorted list of all currently registered plugin identifiers."""
        return sorted(self._plugins)


# Module-level default registry — the pipeline uses this singleton.
# Tests that need isolation should instantiate their own PluginRegistry.
default_registry = PluginRegistry()
