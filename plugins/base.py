# plugins/base.py
# Base class for all Hinata plugins.
# Every plugin must extend this class.

from abc import ABC, abstractmethod
from typing import Any


class BasePlugin(ABC):
    """
    Base class for all Hinata plugins.

    To create a new plugin:
      1. Create a folder in plugins/ with your plugin name
      2. Create plugin.py inside that folder
      3. Extend BasePlugin and implement all abstract methods
      4. The plugin will be auto-discovered on startup

    Example:
        class MyPlugin(BasePlugin):
            name = "my_plugin"
            description = "Does cool stuff"
            version = "1.0.0"

            def get_actions(self) -> dict:
                return {
                    "do_thing": {
                        "description": "Does the thing",
                        "params": {"input": "string - what to process"}
                    }
                }

            async def execute(self, action: str, params: dict) -> Any:
                if action == "do_thing":
                    return f"Did the thing with {params.get('input')}"
    """

    # Override these in your plugin
    name: str = "base_plugin"
    description: str = "Base plugin — do not use directly"
    version: str = "1.0.0"
    enabled: bool = True

    @abstractmethod
    def get_actions(self) -> dict:
        """
        Return a dict of available actions and their descriptions.
        Format: {"action_name": {"description": "...", "params": {"param": "type - desc"}}}
        """
        ...

    @abstractmethod
    async def execute(self, action: str, params: dict) -> Any:
        """
        Execute a specific action with the given parameters.
        Returns the result as a string or dict.
        """
        ...

    def get_description_text(self) -> str:
        """Format plugin info for the LLM context."""
        actions = self.get_actions()
        lines = [f"📦 {self.name} — {self.description}"]
        for action_name, action_info in actions.items():
            desc = action_info.get("description", "")
            params = action_info.get("params", {})
            param_str = ", ".join([f"{k}: {v}" for k, v in params.items()])
            lines.append(f"   • {self.name}.{action_name}({param_str}) — {desc}")
        return "\n".join(lines)
