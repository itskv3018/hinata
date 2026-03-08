# plugins/weather/plugin.py
# Weather information using OpenWeatherMap API or wttr.in (free, no key).

import asyncio
from typing import Any

from config import Config
from plugins.base import BasePlugin
from utils.logger import get_logger

log = get_logger("plugin.weather")


class WeatherPlugin(BasePlugin):
    name = "weather"
    description = "Get current weather, forecasts, and weather alerts for any city"
    version = "1.0.0"

    def get_actions(self) -> dict:
        return {
            "current": {
                "description": "Get current weather for a city",
                "params": {"city": "string - City name (e.g., 'Mumbai', 'New York')"},
            },
            "forecast": {
                "description": "Get 3-day weather forecast",
                "params": {"city": "string - City name"},
            },
        }

    async def execute(self, action: str, params: dict) -> Any:
        city = params.get("city", "").strip()
        if not city:
            return "❌ Please specify a city name"

        if action == "current":
            return await self._get_current(city)
        elif action == "forecast":
            return await self._get_forecast(city)
        return f"Unknown action: {action}"

    async def _get_current(self, city: str) -> str:
        """Get current weather — uses OpenWeatherMap if key available, else wttr.in."""
        if Config.WEATHER_API_KEY:
            return await self._owm_current(city)
        return await self._wttr_current(city)

    async def _get_forecast(self, city: str) -> str:
        if Config.WEATHER_API_KEY:
            return await self._owm_forecast(city)
        return await self._wttr_forecast(city)

    # ------------------------------------------------------------------
    # wttr.in (free, no API key needed)
    # ------------------------------------------------------------------
    async def _wttr_current(self, city: str) -> str:
        import aiohttp
        url = f"https://wttr.in/{city}?format=j1"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status != 200:
                        return f"❌ Could not get weather for {city}"
                    data = await resp.json()

            current = data.get("current_condition", [{}])[0]
            area = data.get("nearest_area", [{}])[0]
            city_name = area.get("areaName", [{}])[0].get("value", city)
            country = area.get("country", [{}])[0].get("value", "")

            temp_c = current.get("temp_C", "?")
            feels_like = current.get("FeelsLikeC", "?")
            humidity = current.get("humidity", "?")
            desc = current.get("weatherDesc", [{}])[0].get("value", "Unknown")
            wind_speed = current.get("windspeedKmph", "?")
            wind_dir = current.get("winddir16Point", "")
            visibility = current.get("visibility", "?")

            weather_emoji = self._get_emoji(desc)

            return (
                f"{weather_emoji} Weather in {city_name}, {country}\n"
                f"  🌡️ Temperature: {temp_c}°C (feels like {feels_like}°C)\n"
                f"  📝 Condition: {desc}\n"
                f"  💧 Humidity: {humidity}%\n"
                f"  💨 Wind: {wind_speed} km/h {wind_dir}\n"
                f"  👁️ Visibility: {visibility} km"
            )
        except Exception as e:
            return f"❌ Weather error: {e}"

    async def _wttr_forecast(self, city: str) -> str:
        import aiohttp
        url = f"https://wttr.in/{city}?format=j1"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    data = await resp.json()

            forecasts = data.get("weather", [])[:3]
            lines = [f"📅 3-Day Forecast for {city}\n"]

            for day in forecasts:
                date = day.get("date", "")
                max_temp = day.get("maxtempC", "?")
                min_temp = day.get("mintempC", "?")
                hourly = day.get("hourly", [])
                desc = hourly[4].get("weatherDesc", [{}])[0].get("value", "Unknown") if len(hourly) > 4 else "Unknown"
                emoji = self._get_emoji(desc)

                lines.append(f"  {emoji} {date}: {min_temp}°C - {max_temp}°C | {desc}")

            return "\n".join(lines)
        except Exception as e:
            return f"❌ Forecast error: {e}"

    # ------------------------------------------------------------------
    # OpenWeatherMap (API key required, more reliable)
    # ------------------------------------------------------------------
    async def _owm_current(self, city: str) -> str:
        import aiohttp
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"q": city, "appid": Config.WEATHER_API_KEY, "units": "metric"}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    return f"❌ Could not get weather for {city}"
                data = await resp.json()

        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        desc = data["weather"][0]["description"].title()
        wind = data["wind"]["speed"]
        emoji = self._get_emoji(desc)

        return (
            f"{emoji} Weather in {data['name']}, {data['sys']['country']}\n"
            f"  🌡️ Temperature: {temp}°C (feels like {feels_like}°C)\n"
            f"  📝 Condition: {desc}\n"
            f"  💧 Humidity: {humidity}%\n"
            f"  💨 Wind: {wind} m/s"
        )

    async def _owm_forecast(self, city: str) -> str:
        import aiohttp
        url = "https://api.openweathermap.org/data/2.5/forecast"
        params = {"q": city, "appid": Config.WEATHER_API_KEY, "units": "metric", "cnt": 24}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                data = await resp.json()

        lines = [f"📅 Forecast for {city}\n"]
        for item in data.get("list", [])[:8]:
            dt = item["dt_txt"]
            temp = item["main"]["temp"]
            desc = item["weather"][0]["description"].title()
            emoji = self._get_emoji(desc)
            lines.append(f"  {emoji} {dt}: {temp}°C | {desc}")

        return "\n".join(lines)

    @staticmethod
    def _get_emoji(description: str) -> str:
        desc = description.lower()
        if "sun" in desc or "clear" in desc:
            return "☀️"
        elif "cloud" in desc or "overcast" in desc:
            return "☁️"
        elif "rain" in desc or "drizzle" in desc:
            return "🌧️"
        elif "snow" in desc:
            return "❄️"
        elif "thunder" in desc or "storm" in desc:
            return "⛈️"
        elif "fog" in desc or "mist" in desc or "haze" in desc:
            return "🌫️"
        return "🌤️"
