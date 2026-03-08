# voice/speaker.py
# Text-to-Speech — converts text responses to spoken audio.
# Supports: Edge TTS (free, high quality), pyttsx3 (offline).

import asyncio
import tempfile
import os
from typing import Optional

from config import Config
from utils.logger import get_logger

log = get_logger("voice.speaker")


class VoiceSpeaker:
    """
    Converts text to speech and plays it.
    Uses Edge TTS (Microsoft, free, natural voices) or pyttsx3 (offline).
    """

    def __init__(self):
        self.engine = Config.TTS_ENGINE
        self.voice = Config.TTS_VOICE
        self.is_speaking = False
        self._pyttsx_engine = None
        log.info(f"Voice speaker initialized (engine: {self.engine}, voice: {self.voice})")

    async def speak(self, text: str):
        """Convert text to speech and play it."""
        if not text:
            return

        self.is_speaking = True
        log.debug(f"Speaking: {text[:80]}...")

        try:
            if self.engine == "edge":
                await self._speak_edge(text)
            elif self.engine == "pyttsx3":
                await asyncio.to_thread(self._speak_pyttsx3, text)
            else:
                await self._speak_edge(text)
        except Exception as e:
            log.error(f"TTS error ({self.engine}): {e}")
            # Fallback to pyttsx3
            try:
                await asyncio.to_thread(self._speak_pyttsx3, text)
            except Exception as e2:
                log.error(f"TTS fallback error: {e2}")
        finally:
            self.is_speaking = False

    async def _speak_edge(self, text: str):
        """Use Microsoft Edge TTS — free, high quality, many voices."""
        try:
            import edge_tts

            # Generate speech
            communicate = edge_tts.Communicate(text, self.voice)

            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp_path = tmp.name

            await communicate.save(tmp_path)

            # Play the audio
            await asyncio.to_thread(self._play_audio, tmp_path)

            # Cleanup
            os.unlink(tmp_path)

        except ImportError:
            log.error("edge-tts not installed. Run: pip install edge-tts")
            raise

    def _speak_pyttsx3(self, text: str):
        """Use pyttsx3 — offline, works everywhere."""
        try:
            import pyttsx3

            if self._pyttsx_engine is None:
                self._pyttsx_engine = pyttsx3.init()
                self._pyttsx_engine.setProperty("rate", 175)
                self._pyttsx_engine.setProperty("volume", 0.9)

            self._pyttsx_engine.say(text)
            self._pyttsx_engine.runAndWait()

        except ImportError:
            log.error("pyttsx3 not installed. Run: pip install pyttsx3")

    def _play_audio(self, filepath: str):
        """Play an audio file."""
        import platform
        os_type = platform.system().lower()

        try:
            # Try pygame first (cross-platform)
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            return
        except ImportError:
            pass

        # OS-specific fallback
        import subprocess
        if os_type == "windows":
            # Use Windows Media Player via PowerShell
            subprocess.run(
                ["powershell", "-c", f"(New-Object Media.SoundPlayer '{filepath}').PlaySync()"],
                capture_output=True,
            )
        elif os_type == "darwin":
            subprocess.run(["afplay", filepath], capture_output=True)
        elif os_type == "linux":
            subprocess.run(["mpg123", filepath], capture_output=True)

    async def list_voices(self) -> list[str]:
        """List available Edge TTS voices."""
        try:
            import edge_tts
            voices = await edge_tts.list_voices()
            return [
                f"{v['ShortName']} ({v['Locale']}) — {v['Gender']}"
                for v in voices
                if v['Locale'].startswith('en')
            ]
        except ImportError:
            return ["edge-tts not installed"]

    def set_voice(self, voice_name: str):
        """Change the TTS voice."""
        self.voice = voice_name
        log.info(f"Voice changed to: {voice_name}")

    def stop(self):
        """Stop speaking."""
        self.is_speaking = False
        try:
            import pygame
            pygame.mixer.music.stop()
        except (ImportError, Exception):
            pass
