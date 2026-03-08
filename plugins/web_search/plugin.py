# plugins/web_search/plugin.py
# Internet search — DuckDuckGo (free, no API key), SerpAPI, or Tavily.

import asyncio
from typing import Any

from config import Config
from plugins.base import BasePlugin
from utils.logger import get_logger

log = get_logger("plugin.web_search")


class WebSearchPlugin(BasePlugin):
    name = "web_search"
    description = "Search the internet for information, news, answers, and websites"
    version = "1.0.0"

    def get_actions(self) -> dict:
        return {
            "search": {
                "description": "Search the web for information",
                "params": {"query": "string - What to search for"},
            },
            "news": {
                "description": "Get latest news on a topic",
                "params": {"topic": "string - News topic"},
            },
            "quick_answer": {
                "description": "Get a quick factual answer (like Google snippet)",
                "params": {"question": "string - A factual question"},
            },
        }

    async def execute(self, action: str, params: dict) -> Any:
        if action == "search":
            return await self._search(params.get("query", ""))
        elif action == "news":
            return await self._news(params.get("topic", ""))
        elif action == "quick_answer":
            return await self._search(params.get("question", ""))
        return f"Unknown action: {action}"

    async def _search(self, query: str) -> str:
        if not query:
            return "❌ Please specify a search query"

        provider = Config.SEARCH_PROVIDER

        if provider == "duckduckgo":
            return await self._search_duckduckgo(query)
        elif provider == "serpapi":
            return await self._search_serpapi(query)
        elif provider == "tavily":
            return await self._search_tavily(query)
        else:
            return await self._search_duckduckgo(query)

    async def _search_duckduckgo(self, query: str) -> str:
        """Free search using DuckDuckGo (no API key needed)."""
        try:
            from duckduckgo_search import DDGS

            def do_search():
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=5))
                    return results

            results = await asyncio.to_thread(do_search)

            if not results:
                return f"🔍 No results found for: {query}"

            lines = [f"🔍 Search results for: {query}\n"]
            for i, r in enumerate(results, 1):
                lines.append(f"{i}. **{r.get('title', 'No title')}**")
                lines.append(f"   {r.get('body', 'No description')[:200]}")
                lines.append(f"   🔗 {r.get('href', '')}\n")

            return "\n".join(lines)

        except ImportError:
            return "❌ duckduckgo-search not installed. Run: pip install duckduckgo-search"
        except Exception as e:
            return f"❌ Search error: {e}"

    async def _search_serpapi(self, query: str) -> str:
        """Search using SerpAPI (requires API key)."""
        import aiohttp

        if not Config.SEARCH_API_KEY:
            return "❌ SEARCH_API_KEY not configured for SerpAPI"

        url = "https://serpapi.com/search.json"
        params = {"q": query, "api_key": Config.SEARCH_API_KEY, "num": 5}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                data = await resp.json()

        results = data.get("organic_results", [])[:5]
        lines = [f"🔍 Search results for: {query}\n"]
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. **{r.get('title', '')}**")
            lines.append(f"   {r.get('snippet', '')[:200]}")
            lines.append(f"   🔗 {r.get('link', '')}\n")

        return "\n".join(lines) if results else f"🔍 No results for: {query}"

    async def _search_tavily(self, query: str) -> str:
        """Search using Tavily AI search (requires API key)."""
        import aiohttp

        if not Config.SEARCH_API_KEY:
            return "❌ SEARCH_API_KEY not configured for Tavily"

        url = "https://api.tavily.com/search"
        payload = {
            "api_key": Config.SEARCH_API_KEY,
            "query": query,
            "max_results": 5,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                data = await resp.json()

        results = data.get("results", [])[:5]
        lines = [f"🔍 Search results for: {query}\n"]
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. **{r.get('title', '')}**")
            lines.append(f"   {r.get('content', '')[:200]}")
            lines.append(f"   🔗 {r.get('url', '')}\n")

        return "\n".join(lines) if results else f"🔍 No results for: {query}"

    async def _news(self, topic: str) -> str:
        """Get latest news using DuckDuckGo news search."""
        if not topic:
            return "❌ Please specify a news topic"

        try:
            from duckduckgo_search import DDGS

            def do_search():
                with DDGS() as ddgs:
                    results = list(ddgs.news(topic, max_results=5))
                    return results

            results = await asyncio.to_thread(do_search)

            if not results:
                return f"📰 No news found for: {topic}"

            lines = [f"📰 Latest news on: {topic}\n"]
            for i, r in enumerate(results, 1):
                lines.append(f"{i}. **{r.get('title', '')}**")
                lines.append(f"   {r.get('body', '')[:200]}")
                lines.append(f"   📅 {r.get('date', '')} | 🔗 {r.get('url', '')}\n")

            return "\n".join(lines)

        except ImportError:
            return "❌ duckduckgo-search not installed. Run: pip install duckduckgo-search"
        except Exception as e:
            return f"❌ News search error: {e}"
