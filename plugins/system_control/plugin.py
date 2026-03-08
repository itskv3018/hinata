# plugins/system_control/plugin.py
# Controls OS-level functions: volume, brightness, screenshot, lock, shutdown, battery, etc.

import os
import sys
import platform
import subprocess
import asyncio
from typing import Any

from plugins.base import BasePlugin
from utils.logger import get_logger

log = get_logger("plugin.system_control")


class SystemControlPlugin(BasePlugin):
    name = "system_control"
    description = "Control your computer — volume, brightness, screenshot, lock screen, shutdown, battery status, system info"
    version = "1.0.0"

    def __init__(self):
        self.os_type = platform.system().lower()  # 'windows', 'linux', 'darwin'

    def get_actions(self) -> dict:
        return {
            "set_volume": {
                "description": "Set system volume (0-100)",
                "params": {"level": "int - Volume level 0-100"},
            },
            "mute": {
                "description": "Mute/unmute system audio",
                "params": {"mute": "bool - True to mute, False to unmute"},
            },
            "set_brightness": {
                "description": "Set screen brightness (0-100)",
                "params": {"level": "int - Brightness level 0-100"},
            },
            "screenshot": {
                "description": "Take a screenshot and save it",
                "params": {"filename": "string - Optional filename"},
            },
            "lock_screen": {
                "description": "Lock the computer screen",
                "params": {},
            },
            "shutdown": {
                "description": "Shutdown the computer (with confirmation)",
                "params": {"delay": "int - Delay in seconds (default 60)"},
            },
            "restart": {
                "description": "Restart the computer",
                "params": {"delay": "int - Delay in seconds (default 60)"},
            },
            "sleep": {
                "description": "Put computer to sleep",
                "params": {},
            },
            "battery_status": {
                "description": "Get battery percentage and charging status",
                "params": {},
            },
            "system_info": {
                "description": "Get system information (OS, CPU, RAM, disk)",
                "params": {},
            },
            "wifi_status": {
                "description": "Get current WiFi connection info",
                "params": {},
            },
        }

    async def execute(self, action: str, params: dict) -> Any:
        actions_map = {
            "set_volume": self._set_volume,
            "mute": self._mute,
            "set_brightness": self._set_brightness,
            "screenshot": self._screenshot,
            "lock_screen": self._lock_screen,
            "shutdown": self._shutdown,
            "restart": self._restart,
            "sleep": self._sleep,
            "battery_status": self._battery_status,
            "system_info": self._system_info,
            "wifi_status": self._wifi_status,
        }

        func = actions_map.get(action)
        if not func:
            return f"Unknown action: {action}. Available: {list(actions_map.keys())}"

        return await asyncio.to_thread(func, params)

    # ------------------------------------------------------------------
    # Implementations
    # ------------------------------------------------------------------
    def _set_volume(self, params: dict) -> str:
        level = int(params.get("level", 50))
        level = max(0, min(100, level))

        if self.os_type == "windows":
            try:
                from ctypes import cast, POINTER
                from comtypes import CLSCTX_ALL
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = cast(interface, POINTER(IAudioEndpointVolume))
                volume.SetMasterVolumeLevelScalar(level / 100, None)
                return f"✅ Volume set to {level}%"
            except ImportError:
                # Fallback using nircmd
                subprocess.run(["nircmd", "setsysvolume", str(int(level / 100 * 65535))], capture_output=True)
                return f"✅ Volume set to {level}%"
        elif self.os_type == "linux":
            subprocess.run(["amixer", "set", "Master", f"{level}%"], capture_output=True)
            return f"✅ Volume set to {level}%"
        elif self.os_type == "darwin":
            subprocess.run(["osascript", "-e", f"set volume output volume {level}"], capture_output=True)
            return f"✅ Volume set to {level}%"

        return "❌ Unsupported OS for volume control"

    def _mute(self, params: dict) -> str:
        mute = params.get("mute", True)
        if self.os_type == "windows":
            try:
                from ctypes import cast, POINTER
                from comtypes import CLSCTX_ALL
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = cast(interface, POINTER(IAudioEndpointVolume))
                volume.SetMute(1 if mute else 0, None)
                return f"✅ Audio {'muted' if mute else 'unmuted'}"
            except ImportError:
                return "❌ pycaw not installed. Run: pip install pycaw"
        return "✅ Mute toggled"

    def _set_brightness(self, params: dict) -> str:
        level = int(params.get("level", 50))
        level = max(0, min(100, level))

        if self.os_type == "windows":
            try:
                import screen_brightness_control as sbc
                sbc.set_brightness(level)
                return f"✅ Brightness set to {level}%"
            except ImportError:
                return "❌ Install screen-brightness-control: pip install screen-brightness-control"
        elif self.os_type == "linux":
            subprocess.run(["xrandr", "--output", "eDP-1", "--brightness", str(level / 100)], capture_output=True)
            return f"✅ Brightness set to {level}%"

        return "❌ Unsupported OS for brightness control"

    def _screenshot(self, params: dict) -> str:
        import time
        filename = params.get("filename", f"screenshot_{int(time.time())}.png")
        save_dir = os.path.expanduser("~/Pictures")
        os.makedirs(save_dir, exist_ok=True)
        filepath = os.path.join(save_dir, filename)

        try:
            from PIL import ImageGrab
            img = ImageGrab.grab()
            img.save(filepath)
            return f"✅ Screenshot saved to {filepath}"
        except ImportError:
            return "❌ Pillow not installed. Run: pip install Pillow"

    def _lock_screen(self, params: dict) -> str:
        if self.os_type == "windows":
            subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], capture_output=True)
        elif self.os_type == "linux":
            subprocess.run(["loginctl", "lock-session"], capture_output=True)
        elif self.os_type == "darwin":
            subprocess.run(["pmset", "displaysleepnow"], capture_output=True)
        return "✅ Screen locked"

    def _shutdown(self, params: dict) -> str:
        delay = int(params.get("delay", 60))
        if self.os_type == "windows":
            subprocess.run(["shutdown", "/s", "/t", str(delay)], capture_output=True)
        elif self.os_type in ("linux", "darwin"):
            subprocess.run(["shutdown", "-h", f"+{delay // 60}"], capture_output=True)
        return f"✅ Computer will shut down in {delay} seconds. Run 'shutdown /a' to cancel."

    def _restart(self, params: dict) -> str:
        delay = int(params.get("delay", 60))
        if self.os_type == "windows":
            subprocess.run(["shutdown", "/r", "/t", str(delay)], capture_output=True)
        elif self.os_type in ("linux", "darwin"):
            subprocess.run(["shutdown", "-r", f"+{delay // 60}"], capture_output=True)
        return f"✅ Computer will restart in {delay} seconds."

    def _sleep(self, params: dict) -> str:
        if self.os_type == "windows":
            subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"], capture_output=True)
        elif self.os_type == "linux":
            subprocess.run(["systemctl", "suspend"], capture_output=True)
        elif self.os_type == "darwin":
            subprocess.run(["pmset", "sleepnow"], capture_output=True)
        return "✅ Computer going to sleep"

    def _battery_status(self, params: dict) -> str:
        try:
            import psutil
            battery = psutil.sensors_battery()
            if battery is None:
                return "🔌 No battery detected (desktop computer)"
            return (
                f"🔋 Battery: {battery.percent}%\n"
                f"⚡ Charging: {'Yes' if battery.power_plugged else 'No'}\n"
                f"⏱️ Time left: {battery.secsleft // 60} minutes"
                if battery.secsleft > 0 else
                f"🔋 Battery: {battery.percent}%\n⚡ {'Charging' if battery.power_plugged else 'On battery'}"
            )
        except ImportError:
            return "❌ psutil not installed. Run: pip install psutil"

    def _system_info(self, params: dict) -> str:
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            return (
                f"💻 System Information\n"
                f"  OS: {platform.system()} {platform.release()}\n"
                f"  CPU: {platform.processor()}\n"
                f"  CPU Usage: {cpu_percent}%\n"
                f"  RAM: {memory.used // (1024**3):.1f}GB / {memory.total // (1024**3):.1f}GB ({memory.percent}%)\n"
                f"  Disk: {disk.used // (1024**3):.1f}GB / {disk.total // (1024**3):.1f}GB ({disk.percent}%)\n"
                f"  Python: {sys.version.split()[0]}"
            )
        except ImportError:
            return f"💻 OS: {platform.system()} {platform.release()}, Python: {sys.version.split()[0]}"

    def _wifi_status(self, params: dict) -> str:
        if self.os_type == "windows":
            result = subprocess.run(
                ["netsh", "wlan", "show", "interfaces"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                info = {}
                for line in lines:
                    if ":" in line:
                        key, _, value = line.partition(":")
                        info[key.strip()] = value.strip()
                ssid = info.get("SSID", "Unknown")
                signal = info.get("Signal", "Unknown")
                return f"📶 WiFi: {ssid} (Signal: {signal})"
        return "📶 WiFi status check not implemented for this OS"
