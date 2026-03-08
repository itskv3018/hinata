# ui/cli.py
# Terminal-based chat interface for Hinata.
# Supports both text and voice interaction.

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from core.agent import HinataAgent
from utils.logger import get_logger

log = get_logger("cli")

# ANSI colors
PURPLE = "\033[95m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"


BANNER = f"""
{PURPLE}{BOLD}
    ██╗  ██╗██╗███╗   ██╗ █████╗ ████████╗ █████╗
    ██║  ██║██║████╗  ██║██╔══██╗╚══██╔══╝██╔══██╗
    ███████║██║██╔██╗ ██║███████║   ██║   ███████║
    ██╔══██║██║██║╚██╗██║██╔══██║   ██║   ██╔══██║
    ██║  ██║██║██║ ╚████║██║  ██║   ██║   ██║  ██║
    ╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝
{RESET}
{CYAN}    🌸 Your Personal AI Agent — v{Config.AGENT_VERSION}{RESET}
{DIM}    Type 'help' for commands | 'quit' to exit | 'voice' for voice mode{RESET}
"""

HELP_TEXT = f"""
{YELLOW}Available Commands:{RESET}
  {GREEN}help{RESET}        — Show this help message
  {GREEN}voice{RESET}       — Toggle voice mode (speak instead of type)
  {GREEN}plugins{RESET}     — List all loaded plugins
  {GREEN}status{RESET}      — Show agent status
  {GREEN}clear{RESET}       — Clear conversation history
  {GREEN}history{RESET}     — Show conversation history
  {GREEN}quit{RESET}        — Exit Hinata

{YELLOW}Just type naturally:{RESET}
  "What's the weather in Mumbai?"
  "Open Chrome"
  "Set a reminder for 5pm to call mom"
  "Take a screenshot"
  "Search for Python tutorials"
  "Play some music on YouTube"
  "What's my battery level?"
"""


async def run_cli():
    """Run the interactive CLI chat interface."""
    print(BANNER)

    # Initialize agent
    print(f"{DIM}  Initializing...{RESET}", end="", flush=True)
    agent = HinataAgent()
    print(f"\r{GREEN}  ✅ {Config.AGENT_NAME} is ready!{RESET}              ")
    print(f"{DIM}  Plugins: {', '.join(agent.plugins.get_all().keys())}{RESET}")
    print()

    voice_mode = False
    speaker = None
    listener = None

    while True:
        try:
            if voice_mode:
                print(f"\n{PURPLE}🎤 Listening...{RESET} (say 'text mode' to switch back)")
                if listener is None:
                    from voice.listener import VoiceListener
                    listener = VoiceListener()
                user_input = await listener.listen(timeout=10, phrase_limit=15)
                if user_input is None:
                    continue
                print(f"{CYAN}You (voice):{RESET} {user_input}")
            else:
                user_input = input(f"\n{CYAN}{BOLD}You:{RESET} ").strip()

            if not user_input:
                continue

            # Handle special commands
            cmd = user_input.lower()

            if cmd in ("quit", "exit", "bye", "goodbye"):
                print(f"\n{PURPLE}🌸 Goodbye! See you next time!{RESET}\n")
                break

            elif cmd == "help":
                print(HELP_TEXT)
                continue

            elif cmd == "voice":
                voice_mode = not voice_mode
                if voice_mode:
                    print(f"{GREEN}🎤 Voice mode enabled!{RESET}")
                    if speaker is None:
                        from voice.speaker import VoiceSpeaker
                        speaker = VoiceSpeaker()
                else:
                    print(f"{GREEN}⌨️ Text mode enabled!{RESET}")
                continue

            elif cmd == "text mode":
                voice_mode = False
                print(f"{GREEN}⌨️ Text mode enabled!{RESET}")
                continue

            elif cmd == "plugins":
                plugins = agent.plugins.list_plugins()
                print(f"\n{YELLOW}📦 Loaded Plugins ({len(plugins)}):{RESET}")
                for p in plugins:
                    print(f"  {GREEN}{p['name']}{RESET} v{p['version']} — {p['description']}")
                    for action in p["actions"]:
                        print(f"    • {action}")
                continue

            elif cmd == "status":
                status = agent.get_status()
                print(f"\n{YELLOW}📊 {Config.AGENT_NAME} Status:{RESET}")
                for k, v in status.items():
                    print(f"  {k}: {v}")
                continue

            elif cmd == "clear":
                agent.short_term.clear()
                print(f"{GREEN}✅ Conversation cleared{RESET}")
                continue

            elif cmd == "history":
                history = agent.short_term.get_history()
                print(f"\n{YELLOW}📜 Conversation History:{RESET}")
                print(history)
                continue

            # Process through the agent
            print(f"{DIM}  🤔 Thinking...{RESET}", end="\r", flush=True)
            response = await agent.process(user_input)
            print(f"                    ", end="\r")  # Clear "thinking..."
            print(f"\n{PURPLE}{BOLD}🌸 {Config.AGENT_NAME}:{RESET} {response}")

            # Speak the response in voice mode
            if voice_mode and speaker:
                await speaker.speak(response)

        except KeyboardInterrupt:
            print(f"\n{PURPLE}🌸 Goodbye!{RESET}\n")
            break
        except EOFError:
            break
        except Exception as e:
            print(f"{RED}❌ Error: {e}{RESET}")
            log.error(f"CLI error: {e}", exc_info=True)


def main():
    """Entry point for CLI."""
    asyncio.run(run_cli())


if __name__ == "__main__":
    main()
