# plugins/media_control/plugin.py
# Media playback control — play/pause, next/prev, open YouTube/Spotify.

import os
import platform
import subprocess
import asyncio
import webbrowser
from typing import Any

from plugins.base import BasePlugin
from utils.logger import get_logger

log = get_logger("plugin.media_control")


class MediaControlPlugin(BasePlugin):
    name = "media_control"
    description = "Control media playback — play/pause music, open YouTube/Spotify, play songs"
    version = "1.0.0"

    def __init__(self):
        self.os_type = platform.system().lower()

    def get_actions(self) -> dict:
        return {
            "play_pause": {
                "description": "Toggle play/pause for current media",
                "params": {},
            },
            "next_track": {
                "description": "Skip to next track",
                "params": {},
            },
            "prev_track": {
                "description": "Go to previous track",
                "params": {},
            },
            "play_youtube": {
                "description": "Search and play a video on YouTube",
                "params": {"query": "string - What to search/play on YouTube"},
            },
            "play_spotify": {
                "description": "Open Spotify and optionally search for a song",
                "params": {"query": "string - Song/artist to search (optional)"},
            },
            "play_music_file": {
                "description": "Play a local music file",
                "params": {"filepath": "string - Path to the music file"},
            },
        }

    async def execute(self, action: str, params: dict) -> Any:
        actions_map = {
            "play_pause": self._play_pause,
            "next_track": self._next_track,
            "prev_track": self._prev_track,
            "play_youtube": self._play_youtube,
            "play_spotify": self._play_spotify,
            "play_music_file": self._play_music_file,
        }

        func = actions_map.get(action)
        if not func:
            return f"Unknown action: {action}"

        return await asyncio.to_thread(func, params)

    def _play_pause(self, params: dict) -> str:
        """Send media play/pause key."""
        if self.os_type == "windows":
            try:
                import ctypes
                # Virtual key code for Media Play/Pause
                VK_MEDIA_PLAY_PAUSE = 0xB3
                ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
                ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 2, 0)
                return "⏯️ Toggled play/pause"
            except Exception as e:
                return f"❌ Could not toggle play/pause: {e}"
        elif self.os_type == "linux":
            subprocess.run(["playerctl", "play-pause"], capture_output=True)
            return "⏯️ Toggled play/pause"
        elif self.os_type == "darwin":
            subprocess.run(
                ["osascript", "-e", 'tell application "System Events" to key code 16 using command down'],
                capture_output=True,
            )
            return "⏯️ Toggled play/pause"
        return "❌ Unsupported OS"

    def _next_track(self, params: dict) -> str:
        if self.os_type == "windows":
            try:
                import ctypes
                VK_MEDIA_NEXT_TRACK = 0xB0
                ctypes.windll.user32.keybd_event(VK_MEDIA_NEXT_TRACK, 0, 0, 0)
                ctypes.windll.user32.keybd_event(VK_MEDIA_NEXT_TRACK, 0, 2, 0)
                return "⏭️ Skipped to next track"
            except Exception:
                pass
        elif self.os_type == "linux":
            subprocess.run(["playerctl", "next"], capture_output=True)
            return "⏭️ Skipped to next track"
        return "⏭️ Next track"

    def _prev_track(self, params: dict) -> str:
        if self.os_type == "windows":
            try:
                import ctypes
                VK_MEDIA_PREV_TRACK = 0xB1
                ctypes.windll.user32.keybd_event(VK_MEDIA_PREV_TRACK, 0, 0, 0)
                ctypes.windll.user32.keybd_event(VK_MEDIA_PREV_TRACK, 0, 2, 0)
                return "⏮️ Previous track"
            except Exception:
                pass
        elif self.os_type == "linux":
            subprocess.run(["playerctl", "previous"], capture_output=True)
            return "⏮️ Previous track"
        return "⏮️ Previous track"

    def _play_youtube(self, params: dict) -> str:
        query = params.get("query", "").strip()
        if not query:
            webbrowser.open("https://youtube.com")
            return "▶️ Opened YouTube"

        # URL-encode the search query
        from urllib.parse import quote
        search_url = f"https://www.youtube.com/results?search_query={quote(query)}"
        webbrowser.open(search_url)
        return f"▶️ Searching YouTube for: {query}"

    def _play_spotify(self, params: dict) -> str:
        query = params.get("query", "").strip()

        if query:
            from urllib.parse import quote
            spotify_url = f"https://open.spotify.com/search/{quote(query)}"
            webbrowser.open(spotify_url)
            return f"🎵 Searching Spotify for: {query}"
        else:
            if self.os_type == "windows":
                subprocess.Popen("start spotify:", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            webbrowser.open("https://open.spotify.com")
            return "🎵 Opened Spotify"

    def _play_music_file(self, params: dict) -> str:
        filepath = params.get("filepath", "").strip()
        if not filepath:
            return "❌ Please specify a music file path"
        if not os.path.exists(filepath):
            return f"❌ File not found: {filepath}"

        if self.os_type == "windows":
            os.startfile(filepath)
        elif self.os_type == "darwin":
            subprocess.Popen(["open", filepath])
        elif self.os_type == "linux":
            subprocess.Popen(["xdg-open", filepath])

        return f"🎵 Playing: {os.path.basename(filepath)}"
