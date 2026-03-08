# memory/short_term.py
# Short-term (conversation) memory — keeps the current session context.

from collections import deque
from datetime import datetime

from config import Config
from utils.logger import get_logger

log = get_logger("memory.short_term")


class ShortTermMemory:
    """
    Stores the current conversation context.
    Acts like a sliding window of recent messages.
    """

    def __init__(self, max_size: int = None):
        self.max_size = max_size or Config.MAX_CONVERSATION_HISTORY
        self._history: deque = deque(maxlen=self.max_size)

    def add(self, role: str, content: str):
        """Add a message to the conversation history."""
        self._history.append({
            "role": role,           # "user" or "assistant"
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })

    def get_history(self, last_n: int = 20) -> str:
        """Get formatted conversation history for LLM context."""
        recent = list(self._history)[-last_n:]
        if not recent:
            return "(No conversation history yet)"

        lines = []
        for msg in recent:
            role = "You" if msg["role"] == "assistant" else "User"
            lines.append(f"{role}: {msg['content']}")
        return "\n".join(lines)

    def get_raw_history(self, last_n: int = None) -> list:
        """Get raw history as list of dicts."""
        history = list(self._history)
        if last_n:
            return history[-last_n:]
        return history

    def clear(self):
        """Clear all conversation history."""
        self._history.clear()
        log.info("Short-term memory cleared")

    def size(self) -> int:
        """Number of messages in memory."""
        return len(self._history)

    def get_last_user_message(self) -> str | None:
        """Get the most recent user message."""
        for msg in reversed(self._history):
            if msg["role"] == "user":
                return msg["content"]
        return None
