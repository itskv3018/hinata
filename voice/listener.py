# voice/listener.py
# Speech-to-Text — converts voice input to text.
# Supports: OpenAI Whisper (local), Google Speech Recognition (cloud).

import asyncio
from typing import Optional

from config import Config
from utils.logger import get_logger

log = get_logger("voice.listener")


class VoiceListener:
    """
    Listens to microphone input and converts speech to text.
    Uses Whisper (local, free) or Google (cloud, free tier).
    """

    def __init__(self):
        self.engine = Config.STT_ENGINE
        self._recognizer = None
        self._microphone = None
        self._whisper_model = None
        self.is_listening = False
        log.info(f"Voice listener initialized (engine: {self.engine})")

    def _init_speech_recognition(self):
        """Lazy init of speech recognition."""
        if self._recognizer is None:
            try:
                import speech_recognition as sr
                self._recognizer = sr.Recognizer()
                self._recognizer.energy_threshold = 300
                self._recognizer.dynamic_energy_threshold = True
                self._recognizer.pause_threshold = 0.8
            except ImportError:
                log.error("speech_recognition not installed. Run: pip install SpeechRecognition")
                raise

    def _init_whisper(self):
        """Lazy init of Whisper model."""
        if self._whisper_model is None:
            try:
                import whisper
                log.info("Loading Whisper model (this may take a moment)...")
                self._whisper_model = whisper.load_model("base")
                log.info("Whisper model loaded")
            except ImportError:
                log.error("OpenAI Whisper not installed. Run: pip install openai-whisper")
                raise

    async def listen(self, timeout: int = 5, phrase_limit: int = 15) -> Optional[str]:
        """
        Listen for speech and return the transcribed text.
        Returns None if nothing was heard or an error occurred.
        """
        return await asyncio.to_thread(self._listen_sync, timeout, phrase_limit)

    def _listen_sync(self, timeout: int = 5, phrase_limit: int = 15) -> Optional[str]:
        """Synchronous listening."""
        import speech_recognition as sr

        self._init_speech_recognition()

        try:
            with sr.Microphone() as source:
                self.is_listening = True
                log.debug("Listening...")

                # Adjust for ambient noise
                self._recognizer.adjust_for_ambient_noise(source, duration=0.5)

                # Listen for speech
                audio = self._recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_limit,
                )

                self.is_listening = False
                log.debug("Processing speech...")

                # Transcribe based on engine
                if self.engine == "whisper":
                    return self._transcribe_whisper(audio)
                else:
                    return self._transcribe_google(audio)

        except sr.WaitTimeoutError:
            self.is_listening = False
            return None
        except sr.UnknownValueError:
            self.is_listening = False
            log.debug("Could not understand audio")
            return None
        except Exception as e:
            self.is_listening = False
            log.error(f"Listening error: {e}")
            return None

    def _transcribe_whisper(self, audio) -> Optional[str]:
        """Transcribe using local Whisper model."""
        import tempfile
        import os

        self._init_whisper()

        # Save audio to temp WAV file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio.get_wav_data())
            tmp_path = tmp.name

        try:
            result = self._whisper_model.transcribe(tmp_path)
            text = result.get("text", "").strip()
            return text if text else None
        finally:
            os.unlink(tmp_path)

    def _transcribe_google(self, audio) -> Optional[str]:
        """Transcribe using Google Speech Recognition (free)."""
        import speech_recognition as sr
        self._init_speech_recognition()

        try:
            text = self._recognizer.recognize_google(audio)
            return text.strip() if text else None
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            log.error(f"Google Speech Recognition error: {e}")
            return None

    async def listen_continuous(self, callback, wake_word: str = None):
        """
        Continuously listen and call the callback with transcribed text.
        If wake_word is set, only trigger callback after hearing it.
        """
        log.info(f"Starting continuous listening" + (f" (wake word: '{wake_word}')" if wake_word else ""))
        self.is_listening = True
        waiting_for_command = False

        while self.is_listening:
            text = await self.listen(timeout=3, phrase_limit=10)
            if text is None:
                continue

            text_lower = text.lower().strip()
            log.debug(f"Heard: {text_lower}")

            if wake_word:
                if wake_word.lower() in text_lower:
                    # Remove wake word from the command
                    command = text_lower.replace(wake_word.lower(), "").strip()
                    if command:
                        await callback(command)
                    else:
                        waiting_for_command = True
                        log.info("Wake word heard, waiting for command...")
                elif waiting_for_command:
                    waiting_for_command = False
                    await callback(text)
            else:
                await callback(text)

    def stop(self):
        """Stop listening."""
        self.is_listening = False
        log.info("Voice listener stopped")
