"""
PharosTracker — orchestrates the stream, filter, and alert pipeline.
"""

import asyncio
import logging
from src.config import load_config
from src.stream import SimulatedStream, PharosWebSocketStream
from src.alerts import AlertPipeline
from src.filters import EventFilter
from src.models import PharosEvent

logger = logging.getLogger("pharos_watch")


class PharosTracker:
    def __init__(self):
        self.config = load_config()
        self.alert_pipeline = AlertPipeline(self.config.discord_webhook_url)
        self.event_filter = EventFilter(self.config)
        self._running = False

        if self.config.simulation_mode:
            logger.warning(
                "⚠️  SIMULATION MODE — events are synthetic. "
                "Set SIMULATION_MODE=false and PHAROS_WS_URL once the Pharos API is live."
            )
            self.stream = SimulatedStream(
                tracked_wallets=self.config.tracked_wallets,
                tracked_contracts=self.config.tracked_contracts,
                interval=self.config.poll_interval,
            )
        else:
            self.stream = PharosWebSocketStream(
                ws_url=self.config.pharos_ws_url,
                tracked_wallets=self.config.tracked_wallets,
                tracked_contracts=self.config.tracked_contracts,
            )

    async def run(self):
        self._running = True

        pipeline_task = asyncio.create_task(self.alert_pipeline.run())
        ingest_task = asyncio.create_task(self._ingest())

        try:
            await asyncio.gather(ingest_task, pipeline_task)
        except asyncio.CancelledError:
            pass
        finally:
            await self.alert_pipeline.stop()

    async def _ingest(self):
        logger.info("📡 Ingestion started — listening for Pharos events...")
        events_seen = 0
        alerts_queued = 0

        async for event in self.stream.events():
            events_seen += 1
            logger.debug(
                f"Event received: {event.event_type.value} | block={event.block_number} | tx={event.short_hash()}"
            )

            if self.event_filter.should_alert(event):
                await self.alert_pipeline.enqueue(event)
                alerts_queued += 1
                logger.info(
                    f"🔔 Alert queued [{event.event_type.value}] tx={event.short_hash()} "
                    f"(queue size: {self.alert_pipeline.queued})"
                )

            if events_seen % 10 == 0:
                logger.info(
                    f"📊 Stats — events seen: {events_seen} | alerts queued: {alerts_queued}"
                )

    async def stop(self):
        logger.info("Shutdown signal received...")
        self.stream.stop()
        self._running = False
