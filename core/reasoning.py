# core/reasoning.py
# LLM reasoning engine — interfaces with Ollama, OpenAI, or Gemini.
# Implements the THINK step of the ReAct loop.

import json
import re
import asyncio
from typing import Optional

from config import Config
from utils.logger import get_logger

log = get_logger("reasoning")


SYSTEM_PROMPT = f"""You are {Config.AGENT_NAME}, an autonomous AI agent that controls the user's devices.

You MUST respond with valid JSON in one of these formats:

1. Direct response (no plugin needed):
{{"action": "respond", "response": "Your natural language response here"}}

2. Execute a single plugin:
{{"action": "execute_plugin", "plugin": "plugin_name", "plugin_action": "action_name", "params": {{"key": "value"}}}}

3. Execute multiple steps:
{{"action": "multi_step", "plan": [{{"plugin": "name", "action": "action", "params": {{}}}}, ...]}}

RULES:
- Always respond with valid JSON, nothing else.
- Pick the most relevant plugin for the task.
- If no plugin is needed, just respond directly.
- Be concise but friendly.
- If you've received observation results, synthesize them into a final response.
"""


class LLMReasoner:
    """Interfaces with LLM providers for reasoning."""

    def __init__(self):
        self.provider = Config.LLM_PROVIDER
        self.model = Config.LLM_MODEL
        log.info(f"Reasoning engine: {self.provider}/{self.model}")

    async def think(self, context: str, observations: list = None) -> dict:
        """
        Send context to LLM and get structured decision back.
        Returns dict with action type and parameters.
        """
        # If we have observations, add them and ask for final response
        if observations:
            obs_text = "\n".join([
                f"- {o['plugin']}.{o['action']} returned: {o['result'][:500]}"
                for o in observations
            ])
            context += f"\n\nPrevious action results:\n{obs_text}\n\nNow synthesize these results into a helpful response for the user."

        # Call the appropriate LLM provider
        try:
            if self.provider == "demo":
                raw = self._demo_response(context)
            elif self.provider == "ollama":
                raw = await self._call_ollama(context)
            elif self.provider == "openai":
                raw = await self._call_openai(context)
            elif self.provider == "gemini":
                raw = await self._call_gemini(context)
            else:
                raw = '{"action": "respond", "response": "LLM provider not configured. Please set LLM_PROVIDER in .env"}'

            # Parse JSON response
            return self._parse_response(raw)

        except Exception as e:
            log.error(f"LLM error: {e}")
            return {"action": "respond", "response": f"I had trouble thinking about that: {str(e)}"}

    # ------------------------------------------------------------------
    # Ollama (local, free, private)
    # ------------------------------------------------------------------
    async def _call_ollama(self, context: str) -> str:
        """Call local Ollama instance."""
        import aiohttp

        url = f"{Config.OLLAMA_BASE_URL}/api/generate"
        payload = {
            "model": self.model,
            "prompt": context,
            "system": SYSTEM_PROMPT,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 1024,
            },
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise Exception(f"Ollama error {resp.status}: {text[:200]}")
                data = await resp.json()
                return data.get("response", "")

    # ------------------------------------------------------------------
    # OpenAI
    # ------------------------------------------------------------------
    async def _call_openai(self, context: str) -> str:
        """Call OpenAI API."""
        import openai

        client = openai.AsyncOpenAI(api_key=Config.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model=Config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": context},
            ],
            temperature=0.7,
            max_tokens=1024,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content

    # ------------------------------------------------------------------
    # Google Gemini
    # ------------------------------------------------------------------
    async def _call_gemini(self, context: str) -> str:
        """Call Google Gemini API."""
        import aiohttp

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{Config.GEMINI_MODEL}:generateContent"
        headers = {"Content-Type": "application/json"}
        params = {"key": Config.GEMINI_API_KEY}
        payload = {
            "contents": [{"parts": [{"text": f"{SYSTEM_PROMPT}\n\n{context}"}]}],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 1024,
                "responseMimeType": "application/json",
            },
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, params=params, headers=headers) as resp:
                data = await resp.json()
                log.debug(f"Gemini raw response keys: {list(data.keys())}")

                if "error" in data:
                    raise Exception(f"Gemini API error: {data['error'].get('message', data['error'])}")

                if "candidates" not in data:
                    # Fallback: maybe blocked or empty
                    log.warning(f"Gemini response has no candidates: {str(data)[:300]}")
                    return '{"action": "respond", "response": "I received an empty response from the AI model. Please try again."}'

                return data["candidates"][0]["content"]["parts"][0]["text"]

    # ------------------------------------------------------------------
    # Response parser
    # ------------------------------------------------------------------
    def _parse_response(self, raw: str) -> dict:
        """Parse LLM JSON response, with fallback for malformed output."""
        raw = raw.strip()

        # Try to extract JSON from the response
        # Sometimes LLMs wrap JSON in markdown code blocks
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()

        try:
            result = json.loads(raw)
            if "action" in result:
                return result
        except json.JSONDecodeError:
            pass

        # Try to find JSON object in the text
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                result = json.loads(raw[start:end])
                if "action" in result:
                    return result
            except json.JSONDecodeError:
                pass

        # Fallback: treat entire response as a direct reply
        log.warning(f"Could not parse LLM response as JSON, using as direct reply")
        return {"action": "respond", "response": raw[:1000]}

    # ------------------------------------------------------------------
    # Demo mode — works offline, no LLM needed
    # ------------------------------------------------------------------
    def _demo_response(self, context: str) -> str:
        """Pattern-match common requests for demo/testing without an LLM."""
        ctx = context.lower()

        # Greetings
        if re.search(r'\b(hello|hi|hey|greetings|good morning|good evening)\b', ctx):
            return json.dumps({"action": "respond", "response": "Hey there! 🌸 I'm Hinata, your personal AI agent. I can control your computer, search the web, manage files, set reminders, take notes, check weather, and much more. Just ask!"})

        # Capabilities
        if re.search(r'what can you do|your (capabilities|features|abilities)|help me with', ctx):
            return json.dumps({"action": "respond", "response": "Here's what I can do 🌸:\n\n🖥️ System Control — volume, brightness, screenshots, battery, lock screen\n🚀 App Launcher — open/close apps, URLs, files\n📁 File Manager — browse, search, create, move, delete files\n🔍 Web Search — search the web via DuckDuckGo\n🌤️ Weather — current weather and forecasts\n📝 Notes — save and manage personal notes\n⏰ Reminders — set reminders and timers\n🎵 Media Control — play/pause music, open YouTube\n\nJust tell me what you need!"})

        # Screenshot
        if re.search(r'screenshot|screen.?shot|capture.?screen', ctx):
            return json.dumps({"action": "execute_plugin", "plugin": "system_control", "plugin_action": "screenshot", "params": {}})

        # Battery
        if re.search(r'battery|power.?level|charge', ctx):
            return json.dumps({"action": "execute_plugin", "plugin": "system_control", "plugin_action": "battery_status", "params": {}})

        # System info
        if re.search(r'system.?info|computer.?info|specs|cpu|ram|memory', ctx):
            return json.dumps({"action": "execute_plugin", "plugin": "system_control", "plugin_action": "system_info", "params": {}})

        # Volume
        m = re.search(r'(set|change)?\s*volume\s*(to\s*)?(\d+)', ctx)
        if m:
            return json.dumps({"action": "execute_plugin", "plugin": "system_control", "plugin_action": "set_volume", "params": {"level": int(m.group(3))}})
        if re.search(r'(mute|unmute|volume)', ctx):
            return json.dumps({"action": "execute_plugin", "plugin": "system_control", "plugin_action": "set_volume", "params": {"level": 50}})

        # Brightness
        m = re.search(r'brightness\s*(to\s*)?(\d+)', ctx)
        if m:
            return json.dumps({"action": "execute_plugin", "plugin": "system_control", "plugin_action": "set_brightness", "params": {"level": int(m.group(2))}})

        # Open apps/URLs
        if re.search(r'open\s+(youtube|chrome|notepad|calculator|spotify|vscode|code)', ctx):
            app = re.search(r'open\s+(\w+)', ctx).group(1)
            return json.dumps({"action": "execute_plugin", "plugin": "app_launcher", "plugin_action": "open_app", "params": {"app_name": app}})

        if re.search(r'open\s+https?://', ctx):
            url = re.search(r'(https?://\S+)', ctx).group(1)
            return json.dumps({"action": "execute_plugin", "plugin": "app_launcher", "plugin_action": "open_url", "params": {"url": url}})

        # Weather
        if re.search(r'weather|temperature|forecast', ctx):
            city_m = re.search(r'(?:weather|temperature|forecast)\s+(?:in|for|at)\s+(.+?)(?:\?|$)', ctx)
            city = city_m.group(1).strip() if city_m else "auto"
            return json.dumps({"action": "execute_plugin", "plugin": "weather", "plugin_action": "current_weather", "params": {"city": city}})

        # Web search
        if re.search(r'search\s+(?:for\s+)?(.+)', ctx):
            query = re.search(r'search\s+(?:for\s+)?(.+?)(?:\?|$)', ctx).group(1).strip()
            return json.dumps({"action": "execute_plugin", "plugin": "web_search", "plugin_action": "search", "params": {"query": query}})

        # Notes
        if re.search(r'(take|add|create|save)\s+(a\s+)?note', ctx):
            content_m = re.search(r'note[:\s]+(.+)', ctx)
            content = content_m.group(1).strip() if content_m else "Untitled note"
            return json.dumps({"action": "execute_plugin", "plugin": "notes", "plugin_action": "add_note", "params": {"title": "Quick Note", "content": content}})
        if re.search(r'(show|list|my)\s+notes', ctx):
            return json.dumps({"action": "execute_plugin", "plugin": "notes", "plugin_action": "list_notes", "params": {}})

        # Reminders
        if re.search(r'(set|create|add)\s+(a\s+)?reminder', ctx):
            return json.dumps({"action": "execute_plugin", "plugin": "reminders", "plugin_action": "add_reminder", "params": {"text": "Reminder from Hinata", "minutes": 5}})

        # Files
        if re.search(r'list\s+files|show\s+files|what.?s in', ctx):
            return json.dumps({"action": "execute_plugin", "plugin": "file_manager", "plugin_action": "list_files", "params": {"path": "."}})

        # Time
        if re.search(r'what.?s the time|current time|what time', ctx):
            from datetime import datetime
            now = datetime.now().strftime("%I:%M %p, %B %d, %Y")
            return json.dumps({"action": "respond", "response": f"It's currently {now} 🕐"})

        # Who are you
        if re.search(r'who are you|your name|about you', ctx):
            return json.dumps({"action": "respond", "response": "I'm Hinata 🌸, your personal AI agent! I was built to be like Jarvis — I can control your computer, search the web, manage files, and learn from how you use me. I get smarter over time!"})

        # Jokes
        if re.search(r'joke|funny|make me laugh', ctx):
            return json.dumps({"action": "respond", "response": "Why do programmers prefer dark mode? Because light attracts bugs! 🐛😄"})

        # Thanks
        if re.search(r'thank|thanks|thx', ctx):
            return json.dumps({"action": "respond", "response": "You're welcome! 🌸 Let me know if you need anything else."})

        # Default
        return json.dumps({"action": "respond", "response": "I understood your message! 🌸 In full mode (with Gemini/Ollama connected), I can reason about complex requests. Right now I'm in demo mode — try asking me to take a screenshot, check the weather, open YouTube, or show system info!"})

