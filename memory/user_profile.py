# memory/user_profile.py
# Learns and stores user preferences, habits, and personal info over time.

import os
import json
from datetime import datetime
from collections import Counter

from config import Config
from utils.logger import get_logger

log = get_logger("memory.user_profile")

PROFILE_FILE = os.path.join(Config.DATA_DIR, "user_profiles.json")


class UserProfile:
    """
    Tracks user preferences and habits.
    Learns from every interaction to personalize responses.
    """

    def __init__(self):
        os.makedirs(Config.DATA_DIR, exist_ok=True)
        self.profiles: dict = self._load()

    def get_or_create(self, user_id: str) -> dict:
        """Get or create a user profile."""
        if user_id not in self.profiles:
            self.profiles[user_id] = {
                "user_id": user_id,
                "name": None,
                "preferences": {},
                "habits": {},
                "interaction_count": 0,
                "topics_discussed": [],
                "first_seen": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat(),
                "favorite_commands": Counter(),
                "active_hours": Counter(),
            }
        return self.profiles[user_id]

    def update_from_interaction(self, user_input: str, user_id: str = "default"):
        """Learn from a user interaction."""
        profile = self.get_or_create(user_id)
        profile["interaction_count"] += 1
        profile["last_seen"] = datetime.now().isoformat()

        # Track active hours
        hour = datetime.now().hour
        if "active_hours" not in profile or not isinstance(profile["active_hours"], dict):
            profile["active_hours"] = {}
        hour_key = str(hour)
        profile["active_hours"][hour_key] = profile["active_hours"].get(hour_key, 0) + 1

        # Extract and learn name if mentioned
        lower_input = user_input.lower()
        if "my name is" in lower_input:
            name = user_input.split("my name is")[-1].strip().split()[0].title()
            profile["name"] = name
            log.info(f"Learned user name: {name}")
        elif "call me" in lower_input:
            name = user_input.split("call me")[-1].strip().split()[0].title()
            profile["name"] = name
            log.info(f"Learned user name: {name}")

        # Track topics (simple keyword extraction)
        keywords = ["weather", "music", "news", "reminder", "note", "file",
                     "search", "app", "volume", "brightness", "screenshot",
                     "timer", "youtube", "spotify"]
        for kw in keywords:
            if kw in lower_input:
                if kw not in profile["topics_discussed"]:
                    profile["topics_discussed"].append(kw)

        self._save()

    def set_preference(self, user_id: str, key: str, value: str):
        """Set a user preference."""
        profile = self.get_or_create(user_id)
        profile["preferences"][key] = value
        self._save()
        log.info(f"Set preference for {user_id}: {key} = {value}")

    def get_preference(self, user_id: str, key: str, default=None):
        """Get a user preference."""
        profile = self.get_or_create(user_id)
        return profile.get("preferences", {}).get(key, default)

    def get_summary(self, user_id: str) -> str:
        """Get a human-readable summary of the user profile."""
        profile = self.get_or_create(user_id)

        name = profile.get("name", "Unknown")
        count = profile.get("interaction_count", 0)
        topics = ", ".join(profile.get("topics_discussed", [])[-10:])
        prefs = profile.get("preferences", {})

        summary = f"Name: {name}, Interactions: {count}"
        if topics:
            summary += f", Interests: {topics}"
        if prefs:
            summary += f", Preferences: {prefs}"

        return summary

    def _load(self) -> dict:
        if os.path.exists(PROFILE_FILE):
            try:
                with open(PROFILE_FILE, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save(self):
        try:
            with open(PROFILE_FILE, "w") as f:
                json.dump(self.profiles, f, indent=2, default=str)
        except IOError as e:
            log.error(f"Failed to save profiles: {e}")
