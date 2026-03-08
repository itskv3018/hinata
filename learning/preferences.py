# learning/preferences.py
# Learns user preferences from interactions.

from utils.logger import get_logger

log = get_logger("learning.preferences")


class PreferenceLearner:
    """
    Extracts preferences from natural conversation.
    E.g., "I prefer dark mode" → stores {"theme": "dark"}
    """

    # Keywords that signal a preference
    PREFERENCE_SIGNALS = [
        "i like", "i love", "i prefer", "i want", "i need",
        "i hate", "i don't like", "i dislike",
        "my favorite", "my preferred",
        "always use", "always play",
        "set my", "change my", "make it",
    ]

    def extract_preferences(self, text: str) -> dict:
        """Extract any preferences from user text."""
        text_lower = text.lower()
        preferences = {}

        for signal in self.PREFERENCE_SIGNALS:
            if signal in text_lower:
                # Extract what comes after the signal
                after = text_lower.split(signal)[-1].strip()
                if after:
                    # Categorize the preference
                    category = self._categorize(after)
                    preferences[category] = after.split(".")[0].strip()[:100]

        return preferences

    def _categorize(self, text: str) -> str:
        """Categorize a preference."""
        categories = {
            "music": ["music", "song", "playlist", "artist", "genre", "spotify", "youtube"],
            "weather": ["weather", "temperature", "city", "location"],
            "language": ["language", "english", "hindi", "spanish"],
            "theme": ["dark", "light", "theme", "color", "mode"],
            "voice": ["voice", "accent", "speed", "volume"],
            "schedule": ["morning", "evening", "night", "time", "schedule"],
        }

        for category, keywords in categories.items():
            if any(kw in text for kw in keywords):
                return category

        return "general"
