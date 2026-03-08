# plugins/file_manager/plugin.py
# File system operations — search, create, read, move, delete files.

import os
import shutil
import glob
import asyncio
from typing import Any
from datetime import datetime

from plugins.base import BasePlugin
from utils.logger import get_logger

log = get_logger("plugin.file_manager")


class FileManagerPlugin(BasePlugin):
    name = "file_manager"
    description = "Manage files and folders — search, create, read, move, delete, list directory contents"
    version = "1.0.0"

    def get_actions(self) -> dict:
        return {
            "list_directory": {
                "description": "List files and folders in a directory",
                "params": {"path": "string - Directory path (default: Desktop)"},
            },
            "search_files": {
                "description": "Search for files by name pattern",
                "params": {
                    "pattern": "string - Search pattern (e.g., '*.pdf', 'report*')",
                    "directory": "string - Where to search (default: home)",
                },
            },
            "read_file": {
                "description": "Read the contents of a text file",
                "params": {"path": "string - File path"},
            },
            "create_file": {
                "description": "Create a new file with content",
                "params": {
                    "path": "string - File path",
                    "content": "string - File content",
                },
            },
            "create_folder": {
                "description": "Create a new folder",
                "params": {"path": "string - Folder path"},
            },
            "move_file": {
                "description": "Move or rename a file/folder",
                "params": {
                    "source": "string - Source path",
                    "destination": "string - Destination path",
                },
            },
            "copy_file": {
                "description": "Copy a file or folder",
                "params": {
                    "source": "string - Source path",
                    "destination": "string - Destination path",
                },
            },
            "delete_file": {
                "description": "Delete a file or folder (moves to recycle bin)",
                "params": {"path": "string - Path to delete"},
            },
            "file_info": {
                "description": "Get detailed info about a file (size, dates, type)",
                "params": {"path": "string - File path"},
            },
            "disk_usage": {
                "description": "Get disk space usage",
                "params": {},
            },
        }

    async def execute(self, action: str, params: dict) -> Any:
        actions_map = {
            "list_directory": self._list_directory,
            "search_files": self._search_files,
            "read_file": self._read_file,
            "create_file": self._create_file,
            "create_folder": self._create_folder,
            "move_file": self._move_file,
            "copy_file": self._copy_file,
            "delete_file": self._delete_file,
            "file_info": self._file_info,
            "disk_usage": self._disk_usage,
        }

        func = actions_map.get(action)
        if not func:
            return f"Unknown action: {action}"

        return await asyncio.to_thread(func, params)

    def _list_directory(self, params: dict) -> str:
        path = params.get("path", os.path.expanduser("~/Desktop"))
        path = os.path.expanduser(path)

        if not os.path.isdir(path):
            return f"❌ Directory not found: {path}"

        items = []
        try:
            for entry in sorted(os.listdir(path)):
                full_path = os.path.join(path, entry)
                if os.path.isdir(full_path):
                    items.append(f"📁 {entry}/")
                else:
                    size = os.path.getsize(full_path)
                    items.append(f"📄 {entry} ({self._format_size(size)})")
        except PermissionError:
            return f"❌ Permission denied: {path}"

        if not items:
            return f"📂 {path} is empty"

        return f"📂 {path}\n" + "\n".join(items[:50])

    def _search_files(self, params: dict) -> str:
        pattern = params.get("pattern", "*")
        directory = params.get("directory", os.path.expanduser("~"))
        directory = os.path.expanduser(directory)

        search_pattern = os.path.join(directory, "**", pattern)
        results = glob.glob(search_pattern, recursive=True)[:20]

        if not results:
            return f"🔍 No files matching '{pattern}' found in {directory}"

        lines = [f"🔍 Found {len(results)} files matching '{pattern}':"]
        for f in results:
            size = os.path.getsize(f) if os.path.isfile(f) else 0
            lines.append(f"  • {f} ({self._format_size(size)})")
        return "\n".join(lines)

    def _read_file(self, params: dict) -> str:
        path = params.get("path", "")
        path = os.path.expanduser(path)
        if not os.path.isfile(path):
            return f"❌ File not found: {path}"

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(10000)  # Limit to 10KB
            if len(content) >= 10000:
                content += "\n\n... (file truncated at 10KB)"
            return f"📄 {path}:\n{content}"
        except Exception as e:
            return f"❌ Could not read file: {e}"

    def _create_file(self, params: dict) -> str:
        path = params.get("path", "")
        content = params.get("content", "")
        path = os.path.expanduser(path)

        if not path:
            return "❌ Please specify a file path"

        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"✅ Created file: {path}"

    def _create_folder(self, params: dict) -> str:
        path = params.get("path", "")
        path = os.path.expanduser(path)
        os.makedirs(path, exist_ok=True)
        return f"✅ Created folder: {path}"

    def _move_file(self, params: dict) -> str:
        source = os.path.expanduser(params.get("source", ""))
        dest = os.path.expanduser(params.get("destination", ""))
        if not os.path.exists(source):
            return f"❌ Source not found: {source}"
        shutil.move(source, dest)
        return f"✅ Moved {source} → {dest}"

    def _copy_file(self, params: dict) -> str:
        source = os.path.expanduser(params.get("source", ""))
        dest = os.path.expanduser(params.get("destination", ""))
        if not os.path.exists(source):
            return f"❌ Source not found: {source}"
        if os.path.isdir(source):
            shutil.copytree(source, dest)
        else:
            shutil.copy2(source, dest)
        return f"✅ Copied {source} → {dest}"

    def _delete_file(self, params: dict) -> str:
        path = os.path.expanduser(params.get("path", ""))
        if not os.path.exists(path):
            return f"❌ Not found: {path}"
        try:
            # Try using send2trash for safe deletion (recycle bin)
            from send2trash import send2trash
            send2trash(path)
            return f"✅ Moved to recycle bin: {path}"
        except ImportError:
            # Fallback: permanent delete
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            return f"✅ Deleted: {path} (permanent — install send2trash for recycle bin support)"

    def _file_info(self, params: dict) -> str:
        path = os.path.expanduser(params.get("path", ""))
        if not os.path.exists(path):
            return f"❌ Not found: {path}"

        stat = os.stat(path)
        is_dir = os.path.isdir(path)
        created = datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
        modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")

        info = (
            f"{'📁' if is_dir else '📄'} {os.path.basename(path)}\n"
            f"  Type: {'Directory' if is_dir else os.path.splitext(path)[1] or 'File'}\n"
            f"  Size: {self._format_size(stat.st_size)}\n"
            f"  Created: {created}\n"
            f"  Modified: {modified}\n"
            f"  Path: {path}"
        )
        return info

    def _disk_usage(self, params: dict) -> str:
        try:
            import psutil
            partitions = psutil.disk_partitions()
            lines = ["💾 Disk Usage:"]
            for p in partitions:
                try:
                    usage = psutil.disk_usage(p.mountpoint)
                    lines.append(
                        f"  {p.device} ({p.mountpoint}): "
                        f"{self._format_size(usage.used)} / {self._format_size(usage.total)} "
                        f"({usage.percent}% used)"
                    )
                except PermissionError:
                    pass
            return "\n".join(lines)
        except ImportError:
            return "❌ psutil not installed"

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} PB"
