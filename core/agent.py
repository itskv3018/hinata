# core/agent.py
# The brain of Hinata — orchestrates reasoning, memory, and plugin execution.
#
# Uses a ReAct (Reason + Act) loop:
#   1. User says something
#   2. Hinata THINKS about what to do
#   3. Hinata DECIDES which plugin/action to use
#   4. Hinata EXECUTES the action
#   5. Hinata OBSERVES the result
#   6. Repeat or respond to user

import json
import time
import asyncio
from typing import Optional

from config import Config
from core.reasoning import LLMReasoner
from core.planner import TaskPlanner
from memory.short_term import ShortTermMemory
from memory.long_term import LongTermMemory
from memory.user_profile import UserProfile
from plugins.registry import PluginRegistry
from utils.logger import get_logger

log = get_logger("agent")


class HinataAgent:
    """
    The main AI agent that processes user input, reasons about it,
    and takes autonomous actions using plugins.
    """

    def __init__(self):
        self.name = Config.AGENT_NAME
        self.version = Config.AGENT_VERSION
        self.start_time = time.time()

        # Core components
        self.reasoner = LLMReasoner()
        self.planner = TaskPlanner()

        # Memory systems
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory()
        self.user_profile = UserProfile()

        # Plugin system
        self.plugins = PluginRegistry()
        self.plugins.discover_and_register()

        log.info(f"🌸 {self.name} v{self.version} initialized")
        log.info(f"   Plugins loaded: {len(self.plugins.get_all())}")
        log.info(f"   LLM: {Config.LLM_PROVIDER}/{Config.LLM_MODEL}")

    # ------------------------------------------------------------------
    # Main entry point — process a user message
    # ------------------------------------------------------------------
    async def process(self, user_input: str, user_id: str = "default") -> str:
        """
        Process a user message through the full ReAct loop.
        Returns the final response string.
        """
        log.info(f"📩 [{user_id}] {user_input[:100]}")

        # Store in short-term memory
        self.short_term.add("user", user_input)

        # Build context for reasoning
        context = self._build_context(user_input, user_id)

        # ReAct loop — think, act, observe (max 5 iterations)
        max_iterations = 5
        observations = []

        for i in range(max_iterations):
            log.debug(f"  ReAct iteration {i + 1}/{max_iterations}")

            # THINK: Ask LLM what to do
            thought = await self.reasoner.think(context, observations)

            if thought.get("action") == "respond":
                # LLM decided it has enough info — respond to user
                response = thought.get("response", "I'm not sure how to help with that.")
                break

            elif thought.get("action") == "execute_plugin":
                # LLM wants to use a plugin
                plugin_name = thought.get("plugin", "")
                action_name = thought.get("plugin_action", "")
                params = thought.get("params", {})

                log.info(f"  ⚡ Executing: {plugin_name}.{action_name}({params})")

                # Execute the plugin action
                result = await self._execute_plugin(plugin_name, action_name, params)
                observations.append({
                    "plugin": plugin_name,
                    "action": action_name,
                    "result": result,
                })

                # Update context with the observation
                context += f"\n\nObservation from {plugin_name}.{action_name}: {result}"

            elif thought.get("action") == "multi_step":
                # LLM wants to execute a plan with multiple steps
                plan = thought.get("plan", [])
                log.info(f"  📋 Executing plan with {len(plan)} steps")

                for step in plan:
                    result = await self._execute_plugin(
                        step.get("plugin", ""),
                        step.get("action", ""),
                        step.get("params", {}),
                    )
                    observations.append({
                        "plugin": step.get("plugin"),
                        "action": step.get("action"),
                        "result": result,
                    })

                context += f"\n\nPlan results: {json.dumps(observations[-len(plan):], default=str)}"

            else:
                response = thought.get("response", "Let me think about that...")
                break
        else:
            # Max iterations reached
            response = "I've been thinking about this extensively. " + observations[-1].get("result", "Here's what I found so far.")

        # Store response in memory
        self.short_term.add("assistant", response)

        # Store in long-term memory for learning
        await self.long_term.store_interaction(user_input, response, user_id)

        # Update user profile based on interaction
        self.user_profile.update_from_interaction(user_input, user_id)

        log.info(f"💬 [{user_id}] Response: {response[:100]}...")
        return response

    # ------------------------------------------------------------------
    # Context builder
    # ------------------------------------------------------------------
    def _build_context(self, user_input: str, user_id: str) -> str:
        """Build the full context string for the LLM."""
        plugin_descriptions = self.plugins.get_descriptions()
        conversation_history = self.short_term.get_history()
        user_info = self.user_profile.get_summary(user_id)

        current_time = time.strftime("%Y-%m-%d %H:%M:%S")

        context = f"""You are {self.name}, a powerful AI assistant that can control the user's phone and laptop.
You are helpful, proactive, and personalized. You learn from every interaction.

Current time: {current_time}
User info: {user_info}

Available plugins and their actions:
{plugin_descriptions}

Recent conversation:
{conversation_history}

User's message: {user_input}

Instructions:
- If you can answer directly from knowledge, respond immediately.
- If you need to use a plugin, specify which one and what action.
- You can chain multiple plugin calls for complex tasks.
- Be natural and conversational — you're a friend, not a robot.
- Remember the user's preferences and habits.
- If the user's request is ambiguous, make your best guess and act.
"""
        return context

    # ------------------------------------------------------------------
    # Plugin execution
    # ------------------------------------------------------------------
    async def _execute_plugin(self, plugin_name: str, action: str, params: dict) -> str:
        """Execute a plugin action and return the result."""
        try:
            plugin = self.plugins.get(plugin_name)
            if not plugin:
                return f"Plugin '{plugin_name}' not found. Available: {list(self.plugins.get_all().keys())}"

            result = await plugin.execute(action, params)
            return str(result)

        except Exception as e:
            log.error(f"Plugin error: {plugin_name}.{action} — {e}")
            return f"Error executing {plugin_name}.{action}: {str(e)}"

    # ------------------------------------------------------------------
    # Quick actions (bypass LLM for speed)
    # ------------------------------------------------------------------
    async def quick_action(self, plugin_name: str, action: str, params: dict = None) -> str:
        """Direct plugin call — skips LLM reasoning for known commands."""
        return await self._execute_plugin(plugin_name, action, params or {})

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------
    def get_status(self) -> dict:
        """Return agent status info."""
        uptime = int(time.time() - self.start_time)
        return {
            "name": self.name,
            "version": self.version,
            "uptime_seconds": uptime,
            "plugins": list(self.plugins.get_all().keys()),
            "plugin_count": len(self.plugins.get_all()),
            "llm_provider": Config.LLM_PROVIDER,
            "llm_model": Config.LLM_MODEL,
            "memory_entries": self.short_term.size(),
        }
