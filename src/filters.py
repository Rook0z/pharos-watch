"""
Filter engine — decides which events should trigger alerts.
Extend rules here as needed.
"""

import logging
from src.models import PharosEvent, EventType
from src.config import Config

logger = logging.getLogger("pharos_watch")


class EventFilter:
    def __init__(self, config: Config):
        self.tracked_wallets = set(w.lower() for w in config.tracked_wallets)
        self.tracked_contracts = set(c.lower() for c in config.tracked_contracts)
        self.min_value = config.min_transfer_value_eth

    def should_alert(self, event: PharosEvent) -> bool:
        """Return True if this event warrants a Discord alert."""

        if event.event_type == EventType.LARGE_TRANSFER:
            return True  # Always alert on large transfers

        if event.event_type in (EventType.WALLET_TRANSFER,):
            return self._check_transfer(event)

        if event.event_type == EventType.CONTRACT_EVENT:
            return self._check_contract_event(event)

        if event.event_type == EventType.CONTRACT_DEPLOY:
            return True  # Always alert on new contract deploys

        return False

    def _check_transfer(self, event: PharosEvent) -> bool:
        # Alert if value exceeds threshold OR involves a tracked wallet
        if event.value_eth and event.value_eth < self.min_value:
            return False

        if self.tracked_wallets:
            from_match = event.from_address and event.from_address.lower() in self.tracked_wallets
            to_match = event.to_address and event.to_address.lower() in self.tracked_wallets
            if not (from_match or to_match):
                logger.debug(f"Transfer skipped — no tracked wallet: {event.short_hash()}")
                return False

        return True

    def _check_contract_event(self, event: PharosEvent) -> bool:
        if self.tracked_contracts:
            addr = event.contract_address
            if not addr or addr.lower() not in self.tracked_contracts:
                logger.debug(f"Contract event skipped — not tracked: {event.short_hash()}")
                return False
        return True
