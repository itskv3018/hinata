# plugins/reminders/plugin.py
# Reminder & alarm system with background scheduling.

import os
import json
import time
import asyncio
import threading
from typing import Any
from datetime import datetime, timedelta

from config import Config
from plugins.base import BasePlugin
from utils.logger import get_logger

log = get_logger("plugin.reminders")

REMINDERS_FILE = os.path.join(Config.DATA_DIR, "reminders.json")


class RemindersPlugin(BasePlugin):
    name = "reminders"
    description = "Set reminders, alarms, and timers. Get notified at the right time."
    version = "1.0.0"

    def __init__(self):
        os.makedirs(Config.DATA_DIR, exist_ok=True)
        self.reminders = self._load_reminders()
        self._callback = None  # Will be set by the agent for notifications
        self._checker_running = False

    def get_actions(self) -> dict:
        return {
            "set_reminder": {
                "description": "Set a reminder for a specific time",
                "params": {
                    "message": "string - What to remind about",
                    "time": "string - When to remind (e.g., '5 minutes', '2 hours', '3pm', '2025-03-15 14:00')",
                },
            },
            "set_timer": {
                "description": "Set a countdown timer",
                "params": {
                    "duration": "string - Timer duration (e.g., '5 minutes', '1 hour', '30 seconds')",
                    "label": "string - Timer label (optional)",
                },
            },
            "list_reminders": {
                "description": "Show all active reminders",
                "params": {},
            },
            "cancel_reminder": {
                "description": "Cancel a reminder by ID",
                "params": {"reminder_id": "string - Reminder ID to cancel"},
            },
        }

    async def execute(self, action: str, params: dict) -> Any:
        actions_map = {
            "set_reminder": self._set_reminder,
            "set_timer": self._set_timer,
            "list_reminders": self._list_reminders,
            "cancel_reminder": self._cancel_reminder,
        }

        func = actions_map.get(action)
        if not func:
            return f"Unknown action: {action}"

        return await asyncio.to_thread(func, params)

    def _set_reminder(self, params: dict) -> str:
        message = params.get("message", "Reminder!")
        time_str = params.get("time", "").strip()

        if not time_str:
            return "❌ Please specify when to remind you"

        # Parse the time
        remind_at = self._parse_time(time_str)
        if not remind_at:
            return f"❌ Could not understand time: '{time_str}'. Try '5 minutes', '3pm', or '2025-03-15 14:00'"

        reminder_id = str(int(time.time() * 1000))[-8:]
        reminder = {
            "id": reminder_id,
            "message": message,
            "remind_at": remind_at.isoformat(),
            "created": datetime.now().isoformat(),
            "type": "reminder",
            "notified": False,
        }
        self.reminders.append(reminder)
        self._save_reminders()
        self._ensure_checker()

        time_diff = remind_at - datetime.now()
        return (
            f"⏰ Reminder set!\n"
            f"  📝 {message}\n"
            f"  🕐 At: {remind_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"  ⏱️ In: {self._format_timedelta(time_diff)}\n"
            f"  ID: {reminder_id}"
        )

    def _set_timer(self, params: dict) -> str:
        duration_str = params.get("duration", "").strip()
        label = params.get("label", "Timer")

        if not duration_str:
            return "❌ Please specify a duration"

        seconds = self._parse_duration(duration_str)
        if seconds <= 0:
            return f"❌ Could not parse duration: '{duration_str}'"

        remind_at = datetime.now() + timedelta(seconds=seconds)
        reminder_id = str(int(time.time() * 1000))[-8:]

        reminder = {
            "id": reminder_id,
            "message": f"⏲️ Timer done: {label}",
            "remind_at": remind_at.isoformat(),
            "created": datetime.now().isoformat(),
            "type": "timer",
            "notified": False,
        }
        self.reminders.append(reminder)
        self._save_reminders()
        self._ensure_checker()

        return (
            f"⏲️ Timer set: {label}\n"
            f"  Duration: {self._format_timedelta(timedelta(seconds=seconds))}\n"
            f"  Fires at: {remind_at.strftime('%H:%M:%S')}\n"
            f"  ID: {reminder_id}"
        )

    def _list_reminders(self, params: dict) -> str:
        active = [r for r in self.reminders if not r.get("notified")]
        if not active:
            return "⏰ No active reminders"

        lines = [f"⏰ Active Reminders ({len(active)}):\n"]
        for r in active:
            remind_at = datetime.fromisoformat(r["remind_at"])
            diff = remind_at - datetime.now()
            status = "⏳" if diff.total_seconds() > 0 else "🔔"
            lines.append(
                f"  {status} [{r['id']}] {r['message']}\n"
                f"      At: {remind_at.strftime('%Y-%m-%d %H:%M')} "
                f"({'in ' + self._format_timedelta(diff) if diff.total_seconds() > 0 else 'OVERDUE'})"
            )

        return "\n".join(lines)

    def _cancel_reminder(self, params: dict) -> str:
        reminder_id = params.get("reminder_id", "").strip()
        for r in self.reminders:
            if r["id"] == reminder_id:
                self.reminders.remove(r)
                self._save_reminders()
                return f"✅ Cancelled reminder: {r['message']}"
        return f"❌ Reminder not found: {reminder_id}"

    # ------------------------------------------------------------------
    # Background checker
    # ------------------------------------------------------------------
    def _ensure_checker(self):
        """Start the background reminder checker if not running."""
        if not self._checker_running:
            self._checker_running = True
            thread = threading.Thread(target=self._check_loop, daemon=True)
            thread.start()
            log.info("Started reminder checker thread")

    def _check_loop(self):
        """Periodically check for due reminders."""
        while self._checker_running:
            now = datetime.now()
            for r in self.reminders:
                if r.get("notified"):
                    continue
                remind_at = datetime.fromisoformat(r["remind_at"])
                if now >= remind_at:
                    r["notified"] = True
                    self._save_reminders()
                    self._notify(r)
            time.sleep(10)  # Check every 10 seconds

    def _notify(self, reminder: dict):
        """Send a notification for a due reminder."""
        log.info(f"🔔 REMINDER: {reminder['message']}")

        # Desktop notification
        try:
            from plyer import notification
            notification.notify(
                title=f"🌸 {Config.AGENT_NAME} Reminder",
                message=reminder["message"],
                timeout=10,
            )
        except ImportError:
            # Fallback: just log it
            print(f"\n🔔 REMINDER: {reminder['message']}\n")

        if self._callback:
            self._callback(reminder)

    # ------------------------------------------------------------------
    # Time parsing
    # ------------------------------------------------------------------
    def _parse_time(self, time_str: str) -> datetime | None:
        """Parse natural language time into a datetime."""
        time_str = time_str.lower().strip()

        # Try relative time first (e.g., "5 minutes", "2 hours")
        seconds = self._parse_duration(time_str)
        if seconds > 0:
            return datetime.now() + timedelta(seconds=seconds)

        # Try common time formats
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%H:%M:%S",
            "%H:%M",
            "%I:%M %p",
            "%I:%M%p",
            "%I %p",
            "%I%p",
        ]

        for fmt in formats:
            try:
                parsed = datetime.strptime(time_str, fmt)
                # If only time was given, assume today
                if parsed.year == 1900:
                    now = datetime.now()
                    parsed = parsed.replace(year=now.year, month=now.month, day=now.day)
                    if parsed < now:
                        parsed += timedelta(days=1)  # Next occurrence
                return parsed
            except ValueError:
                continue

        # Try dateparser if available
        try:
            import dateparser
            result = dateparser.parse(time_str)
            if result:
                return result
        except ImportError:
            pass

        return None

    @staticmethod
    def _parse_duration(duration_str: str) -> int:
        """Parse a duration string into seconds."""
        import re
        duration_str = duration_str.lower().strip()

        total = 0
        patterns = [
            (r"(\d+)\s*(?:s|sec|second)s?", 1),
            (r"(\d+)\s*(?:m|min|minute)s?", 60),
            (r"(\d+)\s*(?:h|hr|hour)s?", 3600),
            (r"(\d+)\s*(?:d|day)s?", 86400),
        ]

        for pattern, multiplier in patterns:
            match = re.search(pattern, duration_str)
            if match:
                total += int(match.group(1)) * multiplier

        return total

    @staticmethod
    def _format_timedelta(td: timedelta) -> str:
        total_seconds = int(td.total_seconds())
        if total_seconds < 0:
            return "overdue"
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        parts = []
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        if seconds and not hours:
            parts.append(f"{seconds}s")
        return " ".join(parts) or "now"

    # Persistence
    def _load_reminders(self) -> list:
        if os.path.exists(REMINDERS_FILE):
            with open(REMINDERS_FILE, "r") as f:
                return json.load(f)
        return []

    def _save_reminders(self):
        with open(REMINDERS_FILE, "w") as f:
            json.dump(self.reminders, f, indent=2)
