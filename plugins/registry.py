# plugins/registry.py
# Auto-discovers and registers all plugins from the plugins/ directory.

import importlib
import pkgutil
import os
from typing import Optional

from plugins.base import BasePlugin
from utils.logger import get_logger

log = get_logger("plugins")


class PluginRegistry:
    """
    Discovers, registers, and manages all Hinata plugins.
    Plugins are auto-loaded from subdirectories of plugins/.
    """

    def __init__(self):
        self._plugins: dict[str, BasePlugin] = {}

    def discover_and_register(self):
        """Scan the plugins directory and load all valid plugins."""
        plugins_dir = os.path.dirname(os.path.abspath(__file__))

        for item in os.listdir(plugins_dir):
            item_path = os.path.join(plugins_dir, item)

            # Skip non-directories and special files
            if not os.path.isdir(item_path) or item.startswith("_"):
                continue

            plugin_file = os.path.join(item_path, "plugin.py")
            if not os.path.exists(plugin_file):
                continue

            try:
                module = importlib.import_module(f"plugins.{item}.plugin")

                # Find the plugin class (subclass of BasePlugin)
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, BasePlugin)
                        and attr is not BasePlugin
                    ):
                        plugin_instance = attr()
                        if plugin_instance.enabled:
                            self._plugins[plugin_instance.name] = plugin_instance
                            log.info(f"  ✅ Loaded plugin: {plugin_instance.name} v{plugin_instance.version}")
                        else:
                            log.info(f"  ⏸️  Skipped disabled plugin: {plugin_instance.name}")
                        break

            except Exception as e:
                log.error(f"  ❌ Failed to load plugin '{item}': {e}")

        log.info(f"Total plugins loaded: {len(self._plugins)}")

    def register(self, plugin: BasePlugin):
        """Manually register a plugin."""
        self._plugins[plugin.name] = plugin
        log.info(f"Registered plugin: {plugin.name}")

    def get(self, name: str) -> Optional[BasePlugin]:
        """Get a plugin by name."""
        return self._plugins.get(name)

    def get_all(self) -> dict[str, BasePlugin]:
        """Get all registered plugins."""
        return self._plugins

    def get_descriptions(self) -> str:
        """Get formatted descriptions of all plugins for LLM context."""
        if not self._plugins:
            return "No plugins loaded."
        return "\n\n".join(
            plugin.get_description_text()
            for plugin in self._plugins.values()
        )

    def list_plugins(self) -> list[dict]:
        """Get a list of all plugins with their info."""
        return [
            {
                "name": p.name,
                "description": p.description,
                "version": p.version,
                "actions": list(p.get_actions().keys()),
            }
            for p in self._plugins.values()
        ]
