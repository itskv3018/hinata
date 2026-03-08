# plugins/__init__.py
from plugins.base import BasePlugin
from plugins.registry import PluginRegistry

__all__ = ["BasePlugin", "PluginRegistry"]
