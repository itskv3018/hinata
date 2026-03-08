# 🌸 Hinata — Your Personal AI Agent

> An autonomous AI assistant that controls your phone and laptop, learns your habits, and gets smarter over time.

## Features

- **🧠 Intelligent Agent** — ReAct reasoning loop with LLM (Ollama/OpenAI/Gemini)
- **🔌 Plugin System** — Extensible architecture, easy to add new capabilities
- **💾 Memory** — Remembers conversations and learns your preferences
- **🎤 Voice Control** — "Hey Hinata" wake word, natural voice interaction
- **📱 Mobile Ready** — WebSocket API for Flutter/React Native mobile app
- **🖥️ Full Device Control** — Volume, brightness, apps, files, screenshots, and more
- **🔍 Internet Search** — DuckDuckGo (free), SerpAPI, or Tavily
- **⏰ Reminders & Notes** — Set alarms, take notes, stay organized
- **🎵 Media Control** — Play/pause music, open YouTube/Spotify
- **📊 Learning Engine** — Detects your patterns and makes proactive suggestions

## Quick Start

### 1. Clone & Setup

```bash
git clone https://github.com/yourusername/hinata.git
cd hinata
pip install -r requirements.txt
cp .env.example .env
```

### 2. Setup LLM (choose one)

**Option A: Ollama (free, local, private — RECOMMENDED)**
```bash
# Install Ollama: https://ollama.ai
ollama pull llama3
```

**Option B: OpenAI**
```bash
# Add to .env:
LLM_PROVIDER=openai
OPENAI_API_KEY=your-key-here
```

**Option C: Google Gemini**
```bash
# Add to .env:
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-key-here
```

### 3. Run Hinata

```bash
# Text chat mode (default)
python main.py

# Voice mode (say "Hey Hinata" to activate)
python main.py --voice

# API server mode (for mobile app)
python main.py --server
```

## Architecture

```
hinata/
├── main.py              # Entry point — CLI, voice, or server mode
├── config.py            # Centralized configuration
├── core/
│   ├── agent.py         # 🧠 Main brain — ReAct reasoning loop
│   ├── reasoning.py     # LLM interface (Ollama/OpenAI/Gemini)
│   └── planner.py       # Multi-step task planning
├── plugins/
│   ├── base.py          # Base plugin class
│   ├── registry.py      # Auto-discovery & registration
│   ├── system_control/  # 🖥️ Volume, brightness, shutdown, battery
│   ├── app_launcher/    # 📱 Open/close apps, URLs, files
│   ├── file_manager/    # 📁 Search, create, read, move files
│   ├── web_search/      # 🔍 Internet search (DuckDuckGo)
│   ├── weather/         # 🌤️ Weather info (wttr.in / OpenWeatherMap)
│   ├── notes/           # 📝 Personal notes system
│   ├── reminders/       # ⏰ Reminders & timers
│   └── media_control/   # 🎵 Play/pause, YouTube, Spotify
├── memory/
│   ├── short_term.py    # 💭 Conversation context
│   ├── long_term.py     # 🧠 ChromaDB vector memory
│   └── user_profile.py  # 👤 User preferences & habits
├── voice/
│   ├── listener.py      # 🎤 Speech-to-Text (Whisper/Google)
│   ├── speaker.py       # 🔊 Text-to-Speech (Edge TTS)
│   └── wake_word.py     # 👂 "Hey Hinata" detection
├── api/
│   └── server.py        # 🌐 FastAPI + WebSocket server
├── ui/
│   └── cli.py           # 💻 Terminal chat interface
└── learning/
    ├── patterns.py      # 📊 Usage pattern detection
    └── preferences.py   # ❤️ Preference learning
```

## Plugins

### Built-in Plugins

| Plugin | Capabilities |
|--------|-------------|
| `system_control` | Volume, brightness, screenshot, lock, shutdown, battery, WiFi, system info |
| `app_launcher` | Open/close apps, URLs, files; list running processes |
| `file_manager` | List, search, create, read, move, copy, delete files & folders |
| `web_search` | Internet search via DuckDuckGo (free), news search |
| `weather` | Current weather & 3-day forecast for any city |
| `notes` | Create, search, list, edit, delete personal notes |
| `reminders` | Set reminders & timers with desktop notifications |
| `media_control` | Play/pause, next/prev track, YouTube, Spotify |

### Creating Your Own Plugin

```python
# plugins/my_plugin/plugin.py
from plugins.base import BasePlugin

class MyPlugin(BasePlugin):
    name = "my_plugin"
    description = "Does amazing things"
    version = "1.0.0"

    def get_actions(self) -> dict:
        return {
            "my_action": {
                "description": "Does the thing",
                "params": {"input": "string - What to process"},
            },
        }

    async def execute(self, action: str, params: dict):
        if action == "my_action":
            return f"Did the thing with {params.get('input')}"
```

Drop it in `plugins/my_plugin/` and it's auto-discovered on startup!

## API Endpoints

When running in server mode (`python main.py --server`):

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Status check |
| `GET` | `/health` | Detailed health info |
| `POST` | `/chat` | Send a message, get a response |
| `POST` | `/plugin` | Directly execute a plugin action |
| `GET` | `/plugins` | List all plugins |
| `WS` | `/ws/{user_id}` | Real-time WebSocket connection |

## Example Conversations

```
You: What's the weather in Mumbai?
🌸 Hinata: ☀️ Weather in Mumbai, India
  🌡️ Temperature: 32°C (feels like 36°C)
  💧 Humidity: 65%
  💨 Wind: 12 km/h SW

You: Open Chrome and search for Python tutorials
🌸 Hinata: ✅ Opened Chrome
  🔍 Here are the top results for "Python tutorials"...

You: Set a reminder for 5pm to call mom
🌸 Hinata: ⏰ Reminder set!
  📝 Call mom
  🕐 At: 2025-03-15 17:00:00
  ⏱️ In: 2h 30m

You: Take a screenshot
🌸 Hinata: ✅ Screenshot saved to ~/Pictures/screenshot_1710504321.png
```

## Roadmap

- [x] Core agent with ReAct reasoning
- [x] Plugin architecture with auto-discovery
- [x] 8 built-in plugins
- [x] Short-term & long-term memory
- [x] Voice input/output
- [x] FastAPI server with WebSocket
- [x] CLI chat interface
- [x] Learning engine
- [ ] Flutter mobile app
- [ ] On-device local LLM (phone)
- [ ] Smart home integration (IoT)
- [ ] Email/calendar plugins
- [ ] Screen reading (OCR + vision)
- [ ] Multi-language support

## License

MIT — Build whatever you want with it.
