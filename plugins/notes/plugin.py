# plugins/notes/plugin.py
# Personal notes system — create, search, list, and delete notes.

import os
import json
import time
import asyncio
from typing import Any
from datetime import datetime

from config import Config
from plugins.base import BasePlugin
from utils.logger import get_logger

log = get_logger("plugin.notes")

NOTES_FILE = os.path.join(Config.DATA_DIR, "notes.json")


class NotesPlugin(BasePlugin):
    name = "notes"
    description = "Take notes, save ideas, create to-do lists, and search your notes"
    version = "1.0.0"

    def __init__(self):
        os.makedirs(Config.DATA_DIR, exist_ok=True)
        self.notes = self._load_notes()

    def get_actions(self) -> dict:
        return {
            "add_note": {
                "description": "Save a new note",
                "params": {
                    "title": "string - Note title",
                    "content": "string - Note content",
                    "tags": "string - Comma-separated tags (optional)",
                },
            },
            "list_notes": {
                "description": "List all saved notes",
                "params": {"tag": "string - Filter by tag (optional)"},
            },
            "search_notes": {
                "description": "Search notes by keyword",
                "params": {"query": "string - Search keyword"},
            },
            "get_note": {
                "description": "Get a specific note by ID or title",
                "params": {"note_id": "string - Note ID or title"},
            },
            "delete_note": {
                "description": "Delete a note by ID",
                "params": {"note_id": "string - Note ID"},
            },
            "edit_note": {
                "description": "Edit an existing note",
                "params": {
                    "note_id": "string - Note ID",
                    "content": "string - New content",
                },
            },
        }

    async def execute(self, action: str, params: dict) -> Any:
        actions_map = {
            "add_note": self._add_note,
            "list_notes": self._list_notes,
            "search_notes": self._search_notes,
            "get_note": self._get_note,
            "delete_note": self._delete_note,
            "edit_note": self._edit_note,
        }

        func = actions_map.get(action)
        if not func:
            return f"Unknown action: {action}"

        return await asyncio.to_thread(func, params)

    def _add_note(self, params: dict) -> str:
        title = params.get("title", "Untitled")
        content = params.get("content", "")
        tags = [t.strip() for t in params.get("tags", "").split(",") if t.strip()]

        note_id = str(int(time.time() * 1000))[-8:]
        note = {
            "id": note_id,
            "title": title,
            "content": content,
            "tags": tags,
            "created": datetime.now().isoformat(),
            "modified": datetime.now().isoformat(),
        }
        self.notes.append(note)
        self._save_notes()
        return f"📝 Note saved! (ID: {note_id})\n  Title: {title}\n  Tags: {', '.join(tags) if tags else 'none'}"

    def _list_notes(self, params: dict) -> str:
        tag_filter = params.get("tag", "").strip().lower()

        notes = self.notes
        if tag_filter:
            notes = [n for n in notes if tag_filter in [t.lower() for t in n.get("tags", [])]]

        if not notes:
            return "📝 No notes found." + (f" (filtered by tag: {tag_filter})" if tag_filter else "")

        lines = [f"📝 Your Notes ({len(notes)} total):\n"]
        for n in notes[-20:]:  # Show last 20
            tags = ", ".join(n.get("tags", []))
            lines.append(f"  [{n['id']}] {n['title']}" + (f" 🏷️ {tags}" if tags else ""))

        return "\n".join(lines)

    def _search_notes(self, params: dict) -> str:
        query = params.get("query", "").lower()
        if not query:
            return "❌ Please specify a search query"

        results = [
            n for n in self.notes
            if query in n.get("title", "").lower()
            or query in n.get("content", "").lower()
            or query in " ".join(n.get("tags", [])).lower()
        ]

        if not results:
            return f"🔍 No notes matching '{query}'"

        lines = [f"🔍 Found {len(results)} notes matching '{query}':\n"]
        for n in results:
            preview = n.get("content", "")[:100]
            lines.append(f"  [{n['id']}] {n['title']}\n    {preview}")

        return "\n".join(lines)

    def _get_note(self, params: dict) -> str:
        note_id = params.get("note_id", "").strip()
        note = self._find_note(note_id)

        if not note:
            return f"❌ Note not found: {note_id}"

        return (
            f"📝 {note['title']}\n"
            f"  ID: {note['id']}\n"
            f"  Created: {note['created']}\n"
            f"  Tags: {', '.join(note.get('tags', []))}\n"
            f"  ---\n"
            f"  {note.get('content', '')}"
        )

    def _delete_note(self, params: dict) -> str:
        note_id = params.get("note_id", "").strip()
        note = self._find_note(note_id)
        if not note:
            return f"❌ Note not found: {note_id}"

        self.notes.remove(note)
        self._save_notes()
        return f"✅ Deleted note: {note['title']} (ID: {note['id']})"

    def _edit_note(self, params: dict) -> str:
        note_id = params.get("note_id", "").strip()
        note = self._find_note(note_id)
        if not note:
            return f"❌ Note not found: {note_id}"

        note["content"] = params.get("content", note["content"])
        note["modified"] = datetime.now().isoformat()
        self._save_notes()
        return f"✅ Updated note: {note['title']}"

    # Helpers
    def _find_note(self, note_id: str):
        for n in self.notes:
            if n["id"] == note_id or n["title"].lower() == note_id.lower():
                return n
        return None

    def _load_notes(self) -> list:
        if os.path.exists(NOTES_FILE):
            with open(NOTES_FILE, "r") as f:
                return json.load(f)
        return []

    def _save_notes(self):
        with open(NOTES_FILE, "w") as f:
            json.dump(self.notes, f, indent=2)
