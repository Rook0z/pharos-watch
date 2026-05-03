"""
Alert pipeline — sends PharosEvents to Discord via webhook.
Includes rate limiting and retry logic.
"""

import asyncio
import logging
import aiohttp
from src.models import PharosEvent

logger = logging.getLogger("pharos_watch")

DISCORD_RATE_LIMIT = 5      # max messages per window
DISCORD_WINDOW_SEC = 2.0    # rate limit window (Discord allows 5/2s per webhook)
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0         # seconds


class AlertPipeline:
    def __init__(self, discord_webhook_url: str):
        self.webhook_url = discord_webhook_url
        print(f"DEBUG webhook URL: '{discord_webhook_url}'")
        self._queue: asyncio.Queue[PharosEvent] = asyncio.Queue()
        self._running = False
        self._sent_count = 0
        self._window_start = 0.0

    async def enqueue(self, event: PharosEvent):
        await self._queue.put(event)

    async def run(self):
        """Drain the queue and send alerts, respecting Discord rate limits."""
        self._running = True
        logger.info("Alert pipeline started")

        async with aiohttp.ClientSession() as session:
            while self._running or not self._queue.empty():
                try:
                    event = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                await self._send_with_retry(session, event)
                self._queue.task_done()

    async def stop(self):
        self._running = False
        await self._queue.join()
        logger.info("Alert pipeline drained and stopped")

    async def _send_with_retry(self, session: aiohttp.ClientSession, event: PharosEvent):
        payload = event.to_discord_embed()

        for attempt in range(1, MAX_RETRIES + 1):
            await self._rate_limit()
            try:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status == 204:
                        logger.info(
                            f"✅ Alert sent [{event.event_type.value}] tx={event.short_hash()}"
                        )
                        self._sent_count += 1
                        return
                    elif resp.status == 429:
                        retry_after = float((await resp.json()).get("retry_after", 2))
                        logger.warning(f"Discord rate limited — waiting {retry_after}s")
                        await asyncio.sleep(retry_after)
                    else:
                        body = await resp.text()
                        logger.error(f"Discord error {resp.status}: {body}")
            except aiohttp.ClientError as e:
                logger.error(f"Network error sending alert (attempt {attempt}): {type(e).__name__}: {e}")

            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_BACKOFF * attempt)

        logger.error(f"❌ Failed to send alert after {MAX_RETRIES} attempts: {event.short_hash()}")

    async def _rate_limit(self):
        """Simple token-bucket rate limiter for Discord."""
        import time
        now = time.monotonic()
        if now - self._window_start >= DISCORD_WINDOW_SEC:
            self._window_start = now
            self._sent_count = 0
        if self._sent_count >= DISCORD_RATE_LIMIT:
            sleep_for = DISCORD_WINDOW_SEC - (now - self._window_start) + 0.1
            if sleep_for > 0:
                await asyncio.sleep(sleep_for)
            self._window_start = time.monotonic()
            self._sent_count = 0

    @property
    def queued(self) -> int:
        return self._queue.qsize()
