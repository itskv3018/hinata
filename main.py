#!/usr/bin/env python3
# main.py
# Entry point for Hinata AI Agent.
# Run: python main.py          → CLI chat mode
# Run: python main.py --server → API server mode
# Run: python main.py --voice  → Voice-activated mode

import sys
import os
import asyncio

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config


def main():
    """Main entry point — parse args and launch the appropriate mode."""
    args = sys.argv[1:]

    # Ensure data directory exists
    os.makedirs(Config.DATA_DIR, exist_ok=True)

    if "--server" in args or "-s" in args:
        # API server mode (for mobile app connection)
        print(f"🌸 Starting {Config.AGENT_NAME} API Server...")
        from api.server import start_server
        start_server()

    elif "--voice" in args or "-v" in args:
        # Voice-activated mode
        print(f"🌸 Starting {Config.AGENT_NAME} in Voice Mode...")
        asyncio.run(run_voice_mode())

    else:
        # Default: CLI chat mode
        from ui.cli import run_cli
        asyncio.run(run_cli())


async def run_voice_mode():
    """Run Hinata in full voice mode with wake word detection."""
    from core.agent import HinataAgent
    from voice.listener import VoiceListener
    from voice.speaker import VoiceSpeaker
    from voice.wake_word import WakeWordDetector

    agent = HinataAgent()
    listener = VoiceListener()
    speaker = VoiceSpeaker()
    wake_detector = WakeWordDetector()

    print(f"🌸 {Config.AGENT_NAME} Voice Mode active!")
    print(f"   Say '{Config.WAKE_WORD}' to activate")
    print(f"   Say 'stop' or 'goodbye' to exit")
    print()

    async def handle_voice_command(text: str):
        """Process a voice command."""
        if text.lower() in ("stop", "goodbye", "exit", "quit"):
            listener.stop()
            wake_detector.stop()
            await speaker.speak("Goodbye! See you next time!")
            return

        print(f"🎤 You: {text}")
        response = await agent.process(text)
        print(f"🌸 {Config.AGENT_NAME}: {response}")
        await speaker.speak(response)

    # Start listening for wake word
    await wake_detector.listen_for_wake_word(listener, handle_voice_command)


if __name__ == "__main__":
    main()
