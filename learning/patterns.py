# learning/patterns.py
# Detects usage patterns and builds proactive suggestions.

import json
import os
from datetime import datetime
from collections import Counter, defaultdict

from config import Config
from utils.logger import get_logger

log = get_logger("learning.patterns")

PATTERNS_FILE = os.path.join(Config.DATA_DIR, "patterns.json")


class PatternDetector:
    """
    Analyzes user behavior over time to detect patterns.
    Enables proactive suggestions like:
    - "You usually check weather at 7am — here's today's forecast"
    - "You always listen to music around this time"
    """

    def __init__(self):
        os.makedirs(Config.DATA_DIR, exist_ok=True)
        self.data = self._load()

    def record_action(self, action: str, plugin: str, user_id: str = "default"):
        """Record a user action with timestamp."""
        now = datetime.now()
        entry = {
            "action": action,
            "plugin": plugin,
            "hour": now.hour,
            "day_of_week": now.strftime("%A"),
            "timestamp": now.isoformat(),
        }

        if user_id not in self.data:
            self.data[user_id] = []
        self.data[user_id].append(entry)

        # Keep last 1000 entries per user
        if len(self.data[user_id]) > 1000:
            self.data[user_id] = self.data[user_id][-1000:]

        self._save()

    def get_suggestions(self, user_id: str = "default") -> list[str]:
        """Get proactive suggestions based on detected patterns."""
        entries = self.data.get(user_id, [])
        if len(entries) < 10:
            return []

        current_hour = datetime.now().hour
        current_day = datetime.now().strftime("%A")

        suggestions = []

        # Find what the user usually does at this hour
        hour_actions = [
            e for e in entries
            if e["hour"] == current_hour
        ]

        if hour_actions:
            action_counts = Counter(e["plugin"] + "." + e["action"] for e in hour_actions)
            most_common = action_counts.most_common(1)
            if most_common and most_common[0][1] >= 3:
                action = most_common[0][0]
                suggestions.append(f"You often use {action} around this time")

        # Day-of-week patterns
        day_actions = [
            e for e in entries
            if e["day_of_week"] == current_day
        ]
        if day_actions:
            day_counts = Counter(e["plugin"] for e in day_actions)
            most_common = day_counts.most_common(1)
            if most_common and most_common[0][1] >= 3:
                plugin = most_common[0][0]
                suggestions.append(f"On {current_day}s, you frequently use {plugin}")

        return suggestions

    def get_frequent_actions(self, user_id: str = "default", top_n: int = 5) -> list:
        """Get the user's most frequent actions."""
        entries = self.data.get(user_id, [])
        if not entries:
            return []

        counts = Counter(f"{e['plugin']}.{e['action']}" for e in entries)
        return counts.most_common(top_n)

    def _load(self) -> dict:
        if os.path.exists(PATTERNS_FILE):
            try:
                with open(PATTERNS_FILE, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save(self):
        with open(PATTERNS_FILE, "w") as f:
            json.dump(self.data, f, indent=2)
