# config.py
# Centralised configuration for Hinata AI Agent.
# All secrets loaded from .env — never hardcode credentials.

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------
    AGENT_NAME: str = "Hinata"
    AGENT_VERSION: str = "0.1.0"
    WAKE_WORD: str = "hey hinata"

    # ------------------------------------------------------------------
    # LLM Provider  —  "ollama" (local) | "openai" | "gemini"
    # ------------------------------------------------------------------
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "llama3")

    # Ollama (runs locally — free, private)
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # OpenAI (cloud fallback)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # Google Gemini
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    # ------------------------------------------------------------------
    # Memory
    # ------------------------------------------------------------------
    CHROMA_DB_PATH: str = os.getenv("CHROMA_DB_PATH", "./data/memory")
    SQLITE_DB_PATH: str = os.getenv("SQLITE_DB_PATH", "./data/hinata.db")
    MAX_CONVERSATION_HISTORY: int = int(os.getenv("MAX_CONVERSATION_HISTORY", "50"))

    # ------------------------------------------------------------------
    # Voice
    # ------------------------------------------------------------------
    STT_ENGINE: str = os.getenv("STT_ENGINE", "whisper")       # whisper | google
    TTS_ENGINE: str = os.getenv("TTS_ENGINE", "edge")          # edge | pyttsx3
    TTS_VOICE: str = os.getenv("TTS_VOICE", "en-US-AriaNeural")
    VOICE_ENABLED: bool = os.getenv("VOICE_ENABLED", "true").lower() == "true"

    # ------------------------------------------------------------------
    # API Server
    # ------------------------------------------------------------------
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    SECRET_KEY: str = os.getenv("SECRET_KEY", "hinata-secret-change-me")

    # ------------------------------------------------------------------
    # External APIs (for plugins)
    # ------------------------------------------------------------------
    WEATHER_API_KEY: str = os.getenv("WEATHER_API_KEY", "")           # OpenWeatherMap
    SEARCH_API_KEY: str = os.getenv("SEARCH_API_KEY", "")             # SerpAPI / Tavily
    SEARCH_PROVIDER: str = os.getenv("SEARCH_PROVIDER", "duckduckgo") # duckduckgo | serpapi | tavily

    # ------------------------------------------------------------------
    # System
    # ------------------------------------------------------------------
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    DATA_DIR: str = os.getenv("DATA_DIR", "./data")
    PLUGINS_DIR: str = os.getenv("PLUGINS_DIR", "./plugins")
