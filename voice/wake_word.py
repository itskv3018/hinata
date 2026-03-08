# voice/wake_word.py
# Wake word detection — "Hey Hinata" activation.

import asyncio
from typing import Callable

from config import Config
from utils.logger import get_logger

log = get_logger("voice.wake_word")


class WakeWordDetector:
    """
    Detects the wake word "Hey Hinata" to activate the agent.
    Uses simple keyword matching on STT output.
    For production, could use Porcupine or Snowboy for always-on detection.
    """

    def __init__(self, wake_word: str = None):
        self.wake_word = (wake_word or Config.WAKE_WORD).lower()
        self.is_active = False
        self.alternatives = [
            self.wake_word,
            "hey hinata",
            "hi hinata",
            "ok hinata",
            "hinata",
        ]
        log.info(f"Wake word detector: '{self.wake_word}'")

    def check(self, text: str) -> tuple[bool, str]:
        """
        Check if text contains the wake word.
        Returns (triggered, remaining_command).
        """
        text_lower = text.lower().strip()

        for alt in self.alternatives:
            if alt in text_lower:
                # Remove wake word and return the command
                command = text_lower
                for a in self.alternatives:
                    command = command.replace(a, "").strip()
                return True, command

        return False, ""

    async def listen_for_wake_word(self, listener, callback: Callable):
        """
        Continuously listen for the wake word using the voice listener.
        When detected, call the callback with the command.
        """
        log.info(f"Listening for wake word: '{self.wake_word}'")
        self.is_active = True

        while self.is_active:
            text = await listener.listen(timeout=3, phrase_limit=10)
            if text is None:
                continue

            triggered, command = self.check(text)
            if triggered:
                log.info(f"🌸 Wake word detected! Command: '{command}'")
                if command:
                    await callback(command)
                else:
                    # Wake word only — wait for the actual command
                    log.info("Waiting for command...")
                    command_text = await listener.listen(timeout=5, phrase_limit=15)
                    if command_text:
                        await callback(command_text)

    def stop(self):
        """Stop listening for wake word."""
        self.is_active = False
