import os
from dataclasses import dataclass, field
from typing import List
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    # Discord
    discord_webhook_url: str = field(
        default_factory=lambda: os.getenv("DISCORD_WEBHOOK_URL", "")
    )

    # Pharos RPC / WebSocket (swap these out when Pharos API goes live)
    pharos_ws_url: str = field(
        default_factory=lambda: os.getenv(
            "PHAROS_WS_URL", "wss://placeholder.pharos.network/ws"
        )
    )
    pharos_rpc_url: str = field(
        default_factory=lambda: os.getenv(
            "PHAROS_RPC_URL", "https://placeholder.pharos.network/rpc"
        )
    )

    # Wallets to track
    tracked_wallets: List[str] = field(
        default_factory=lambda: [
            w.strip()
            for w in os.getenv("TRACKED_WALLETS", "").split(",")
            if w.strip()
        ]
    )

    # Contracts to track
    tracked_contracts: List[str] = field(
        default_factory=lambda: [
            c.strip()
            for c in os.getenv("TRACKED_CONTRACTS", "").split(",")
            if c.strip()
        ]
    )

    # Alert thresholds
    min_transfer_value_eth: float = field(
        default_factory=lambda: float(os.getenv("MIN_TRANSFER_VALUE_ETH", "0.01"))
    )

    # Simulation mode (True until Pharos API is live)
    simulation_mode: bool = field(
        default_factory=lambda: os.getenv("SIMULATION_MODE", "true").lower() == "true"
    )

    # Polling interval (seconds) — used when WS not available
    poll_interval: int = field(
        default_factory=lambda: int(os.getenv("POLL_INTERVAL", "5"))
    )


def load_config() -> Config:
    return Config()
