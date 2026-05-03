#!/usr/bin/env python3
"""
PharosWatch - Real-time Pharos Network Event Tracker
Monitors wallet activity and smart contract events with Discord alerts.
"""

import asyncio
import logging
import signal
import sys
import platform
from src.tracker import PharosTracker
from src.logger import setup_logger

logger = setup_logger("pharos_watch")


async def main():
    logger.info("PharosWatch starting up...")
    tracker = PharosTracker()

    # add_signal_handler is Unix-only; use KeyboardInterrupt on Windows
    if platform.system() != "Windows":
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(tracker.stop()))

    await tracker.run()
    logger.info("PharosWatch shut down cleanly.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted — shutting down.")
        sys.exit(0)