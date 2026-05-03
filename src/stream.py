"""
Stream module — generates simulated Pharos events now.
Replace SimulatedStream with PharosWebSocketStream once the Pharos API is live.
"""

import asyncio
import random
import string
import logging
from typing import AsyncIterator
from src.models import PharosEvent, EventType

logger = logging.getLogger("pharos_watch")

# ─── helpers ──────────────────────────────────────────────────────────────────

def _rand_addr() -> str:
    return "0x" + "".join(random.choices("0123456789abcdef", k=40))

def _rand_hash() -> str:
    return "0x" + "".join(random.choices("0123456789abcdef", k=64))

SAMPLE_EVENTS = [
    ("Transfer", {"from": None, "to": None, "value": None}),
    ("Swap",     {"token_in": "USDC", "token_out": "ETH", "amount_in": None}),
    ("Mint",     {"to": None, "amount": None}),
    ("Burn",     {"from": None, "amount": None}),
    ("Approval", {"owner": None, "spender": None, "value": None}),
]

CONTRACT_ADDRS = [_rand_addr() for _ in range(5)]

# ─── simulated stream ──────────────────────────────────────────────────────────

class SimulatedStream:
    """
    Yields fake Pharos events on a ticker.
    Swap out for PharosWebSocketStream when API is live.
    """

    def __init__(self, tracked_wallets: list, tracked_contracts: list, interval: float = 4.0):
        self.tracked_wallets = tracked_wallets or [_rand_addr() for _ in range(3)]
        self.tracked_contracts = tracked_contracts or CONTRACT_ADDRS
        self.interval = interval
        self._running = False
        self._block = random.randint(1_000_000, 2_000_000)

    async def events(self) -> AsyncIterator[PharosEvent]:
        self._running = True
        logger.info(f"[SIM] Stream started — emitting every {self.interval}s")

        while self._running:
            await asyncio.sleep(self.interval + random.uniform(-1, 1))
            self._block += random.randint(1, 3)
            event = self._generate_event()
            if event:
                yield event

    def stop(self):
        self._running = False

    def _generate_event(self) -> PharosEvent | None:
        roll = random.random()

        if roll < 0.40:
            return self._wallet_transfer()
        elif roll < 0.70:
            return self._contract_event()
        elif roll < 0.85:
            return self._large_transfer()
        else:
            return self._contract_deploy()

    def _wallet_transfer(self) -> PharosEvent:
        from_addr = random.choice(self.tracked_wallets + [_rand_addr()])
        to_addr = random.choice(self.tracked_wallets + [_rand_addr()])
        value = round(random.uniform(0.001, 5.0), 4)
        return PharosEvent(
            event_type=EventType.WALLET_TRANSFER,
            tx_hash=_rand_hash(),
            block_number=self._block,
            from_address=from_addr,
            to_address=to_addr,
            value_eth=value,
            token_symbol=random.choice(["ETH", "USDC", "PHAR"]),
            simulated=True,
        )

    def _large_transfer(self) -> PharosEvent:
        from_addr = _rand_addr()
        to_addr = random.choice(self.tracked_wallets + [_rand_addr()])
        value = round(random.uniform(10.0, 500.0), 2)
        return PharosEvent(
            event_type=EventType.LARGE_TRANSFER,
            tx_hash=_rand_hash(),
            block_number=self._block,
            from_address=from_addr,
            to_address=to_addr,
            value_eth=value,
            token_symbol=random.choice(["ETH", "PHAR"]),
            simulated=True,
        )

    def _contract_event(self) -> PharosEvent:
        name, template = random.choice(SAMPLE_EVENTS)
        data = {k: str(round(random.uniform(0.1, 1000), 2)) if v is None else v
                for k, v in template.items()}
        return PharosEvent(
            event_type=EventType.CONTRACT_EVENT,
            tx_hash=_rand_hash(),
            block_number=self._block,
            contract_address=random.choice(self.tracked_contracts),
            event_name=name,
            event_data=data,
            simulated=True,
        )

    def _contract_deploy(self) -> PharosEvent:
        return PharosEvent(
            event_type=EventType.CONTRACT_DEPLOY,
            tx_hash=_rand_hash(),
            block_number=self._block,
            contract_address=_rand_addr(),
            from_address=random.choice(self.tracked_wallets + [_rand_addr()]),
            simulated=True,
        )


# ─── real WebSocket stream (plug in when Pharos API is live) ──────────────────

class PharosWebSocketStream:
    """
    TODO: Replace SimulatedStream with this once Pharos exposes a public WS endpoint.

    Expected Pharos WS message format (placeholder — update to match real schema):
    {
        "type": "transaction" | "event",
        "hash": "0x...",
        "blockNumber": 123456,
        "from": "0x...",
        "to": "0x...",
        "value": "1000000000000000000",   # wei
        "contractAddress": "0x..." | null,
        "eventName": "Transfer" | null,
        "eventData": { ... } | null
    }
    """

    def __init__(self, ws_url: str, tracked_wallets: list, tracked_contracts: list):
        self.ws_url = ws_url
        self.tracked_wallets = set(w.lower() for w in tracked_wallets)
        self.tracked_contracts = set(c.lower() for c in tracked_contracts)
        self._running = False

    async def events(self) -> AsyncIterator[PharosEvent]:
        import websockets, json
        self._running = True
        logger.info(f"Connecting to Pharos WS: {self.ws_url}")

        async with websockets.connect(self.ws_url) as ws:
            # Subscribe to relevant topics (update subscription format to match Pharos docs)
            await ws.send(json.dumps({
                "action": "subscribe",
                "topics": ["transactions", "events"],
                "wallets": list(self.tracked_wallets),
                "contracts": list(self.tracked_contracts),
            }))

            async for raw in ws:
                if not self._running:
                    break
                try:
                    msg = json.loads(raw)
                    event = self._parse(msg)
                    if event:
                        yield event
                except Exception as e:
                    logger.warning(f"Failed to parse WS message: {e}")

    def stop(self):
        self._running = False

    def _parse(self, msg: dict) -> PharosEvent | None:
        # TODO: Map real Pharos message schema to PharosEvent
        # This is a placeholder — update field names to match actual Pharos API
        try:
            value_wei = int(msg.get("value", "0"))
            value_eth = value_wei / 1e18

            return PharosEvent(
                event_type=EventType.CONTRACT_EVENT if msg.get("eventName") else EventType.WALLET_TRANSFER,
                tx_hash=msg["hash"],
                block_number=int(msg["blockNumber"]),
                from_address=msg.get("from"),
                to_address=msg.get("to"),
                value_eth=value_eth,
                contract_address=msg.get("contractAddress"),
                event_name=msg.get("eventName"),
                event_data=msg.get("eventData"),
                simulated=False,
            )
        except KeyError as e:
            logger.warning(f"Missing field in WS message: {e}")
            return None
