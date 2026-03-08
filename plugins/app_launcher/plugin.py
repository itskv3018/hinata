# plugins/app_launcher/plugin.py
# Launch, close, and manage applications on the user's computer.

import os
import sys
import platform
import subprocess
import asyncio
from typing import Any

from plugins.base import BasePlugin
from utils.logger import get_logger

log = get_logger("plugin.app_launcher")


# Common app aliases → actual executable names/paths (Windows)
WINDOWS_APPS = {
    "chrome": "chrome",
    "google chrome": "chrome",
    "firefox": "firefox",
    "brave": "brave",
    "edge": "msedge",
    "notepad": "notepad",
    "calculator": "calc",
    "paint": "mspaint",
    "file explorer": "explorer",
    "explorer": "explorer",
    "cmd": "cmd",
    "terminal": "wt",
    "powershell": "powershell",
    "vscode": "code",
    "vs code": "code",
    "visual studio code": "code",
    "spotify": "spotify",
    "discord": "discord",
    "slack": "slack",
    "teams": "teams",
    "zoom": "zoom",
    "word": "winword",
    "excel": "excel",
    "powerpoint": "powerpnt",
    "outlook": "outlook",
    "task manager": "taskmgr",
    "settings": "ms-settings:",
    "control panel": "control",
    "snipping tool": "snippingtool",
    "camera": "microsoft.windows.camera:",
    "photos": "ms-photos:",
    "maps": "bingmaps:",
    "store": "ms-windows-store:",
    "clock": "ms-clock:",
    "weather": "bingweather:",
    "mail": "outlookmail:",
    "calendar": "outlookcal:",
    "whatsapp": "whatsapp:",
}


class AppLauncherPlugin(BasePlugin):
    name = "app_launcher"
    description = "Open, close, and manage applications on your computer"
    version = "1.0.0"

    def __init__(self):
        self.os_type = platform.system().lower()

    def get_actions(self) -> dict:
        return {
            "open_app": {
                "description": "Open/launch an application",
                "params": {"app_name": "string - Name of the app to open"},
            },
            "close_app": {
                "description": "Close a running application",
                "params": {"app_name": "string - Name of the app to close"},
            },
            "list_running": {
                "description": "List currently running applications",
                "params": {},
            },
            "open_url": {
                "description": "Open a URL in the default browser",
                "params": {"url": "string - URL to open"},
            },
            "open_file": {
                "description": "Open a file with its default application",
                "params": {"filepath": "string - Path to the file"},
            },
        }

    async def execute(self, action: str, params: dict) -> Any:
        actions_map = {
            "open_app": self._open_app,
            "close_app": self._close_app,
            "list_running": self._list_running,
            "open_url": self._open_url,
            "open_file": self._open_file,
        }

        func = actions_map.get(action)
        if not func:
            return f"Unknown action: {action}"

        return await asyncio.to_thread(func, params)

    def _open_app(self, params: dict) -> str:
        app_name = params.get("app_name", "").lower().strip()
        if not app_name:
            return "❌ Please specify an app name"

        # Resolve alias
        executable = WINDOWS_APPS.get(app_name, app_name)

        try:
            if self.os_type == "windows":
                # Try as a UWP app (URI scheme)
                if executable.endswith(":"):
                    os.startfile(executable)
                else:
                    subprocess.Popen(
                        f"start {executable}",
                        shell=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
            elif self.os_type == "darwin":
                subprocess.Popen(["open", "-a", app_name])
            elif self.os_type == "linux":
                subprocess.Popen([executable], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            return f"✅ Opened {app_name}"
        except Exception as e:
            return f"❌ Could not open {app_name}: {e}"

    def _close_app(self, params: dict) -> str:
        app_name = params.get("app_name", "").lower().strip()
        if not app_name:
            return "❌ Please specify an app name"

        executable = WINDOWS_APPS.get(app_name, app_name)

        try:
            if self.os_type == "windows":
                # Try common exe names
                result = subprocess.run(
                    ["taskkill", "/IM", f"{executable}.exe", "/F"],
                    capture_output=True, text=True,
                )
                if result.returncode == 0:
                    return f"✅ Closed {app_name}"
                else:
                    return f"❌ Could not close {app_name}: {result.stderr.strip()}"
            elif self.os_type in ("linux", "darwin"):
                subprocess.run(["pkill", "-f", app_name], capture_output=True)
                return f"✅ Closed {app_name}"
        except Exception as e:
            return f"❌ Error closing {app_name}: {e}"

    def _list_running(self, params: dict) -> str:
        try:
            import psutil
            processes = []
            seen = set()
            for proc in psutil.process_iter(["name", "pid", "memory_percent"]):
                name = proc.info["name"]
                if name and name not in seen and proc.info["memory_percent"] > 0.1:
                    seen.add(name)
                    processes.append({
                        "name": name,
                        "pid": proc.info["pid"],
                        "memory": f"{proc.info['memory_percent']:.1f}%",
                    })

            processes.sort(key=lambda x: float(x["memory"].rstrip("%")), reverse=True)
            top_apps = processes[:15]
            lines = ["📱 Running Applications (top 15 by memory):"]
            for app in top_apps:
                lines.append(f"  • {app['name']} (PID: {app['pid']}, RAM: {app['memory']})")
            return "\n".join(lines)
        except ImportError:
            return "❌ psutil not installed. Run: pip install psutil"

    def _open_url(self, params: dict) -> str:
        url = params.get("url", "").strip()
        if not url:
            return "❌ Please specify a URL"
        if not url.startswith("http"):
            url = "https://" + url

        import webbrowser
        webbrowser.open(url)
        return f"✅ Opened {url} in browser"

    def _open_file(self, params: dict) -> str:
        filepath = params.get("filepath", "").strip()
        if not filepath:
            return "❌ Please specify a file path"
        if not os.path.exists(filepath):
            return f"❌ File not found: {filepath}"

        if self.os_type == "windows":
            os.startfile(filepath)
        elif self.os_type == "darwin":
            subprocess.Popen(["open", filepath])
        elif self.os_type == "linux":
            subprocess.Popen(["xdg-open", filepath])

        return f"✅ Opened {filepath}"
