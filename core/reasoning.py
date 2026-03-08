# core/reasoning.py
# LLM reasoning engine — interfaces with Ollama, OpenAI, or Gemini.
# Implements the THINK step of the ReAct loop.

import json
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
            if self.provider == "ollama":
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
