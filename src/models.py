from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import time


class EventType(str, Enum):
    WALLET_TRANSFER = "wallet_transfer"
    CONTRACT_EVENT = "contract_event"
    LARGE_TRANSFER = "large_transfer"
    CONTRACT_DEPLOY = "contract_deploy"


@dataclass
class PharosEvent:
    event_type: EventType
    tx_hash: str
    block_number: int
    timestamp: float = field(default_factory=time.time)

    # Wallet transfer fields
    from_address: Optional[str] = None
    to_address: Optional[str] = None
    value_eth: Optional[float] = None
    token_symbol: Optional[str] = None

    # Contract event fields
    contract_address: Optional[str] = None
    event_name: Optional[str] = None
    event_data: Optional[dict] = None

    # Meta
    simulated: bool = False

    def short_hash(self) -> str:
        return f"{self.tx_hash[:6]}...{self.tx_hash[-4:]}"

    def short_addr(self, addr: str) -> str:
        if not addr:
            return "unknown"
        return f"{addr[:6]}...{addr[-4:]}"

    def to_discord_embed(self) -> dict:
        """Render event as a Discord embed payload."""
        if self.event_type in (EventType.WALLET_TRANSFER, EventType.LARGE_TRANSFER):
            return self._transfer_embed()
        elif self.event_type == EventType.CONTRACT_EVENT:
            return self._contract_embed()
        elif self.event_type == EventType.CONTRACT_DEPLOY:
            return self._deploy_embed()
        return self._generic_embed()

    def _transfer_embed(self) -> dict:
        is_large = self.event_type == EventType.LARGE_TRANSFER
        color = 0xFF4444 if is_large else 0x00BFFF
        title = "🚨 Large Transfer Detected" if is_large else "💸 Wallet Transfer"
        return {
            "embeds": [
                {
                    "title": title,
                    "color": color,
                    "fields": [
                        {"name": "From", "value": f"`{self.short_addr(self.from_address)}`", "inline": True},
                        {"name": "To", "value": f"`{self.short_addr(self.to_address)}`", "inline": True},
                        {"name": "Amount", "value": f"`{self.value_eth:.4f} {self.token_symbol or 'ETH'}`", "inline": True},
                        {"name": "Tx Hash", "value": f"`{self.short_hash()}`", "inline": True},
                        {"name": "Block", "value": f"`#{self.block_number}`", "inline": True},
                        {"name": "Network", "value": "`Pharos`", "inline": True},
                    ],
                    "footer": {
                        "text": f"PharosWatch {'[SIM] ' if self.simulated else ''}• Block #{self.block_number}"
                    },
                }
            ]
        }

    def _contract_embed(self) -> dict:
        fields = [
            {"name": "Contract", "value": f"`{self.short_addr(self.contract_address)}`", "inline": True},
            {"name": "Event", "value": f"`{self.event_name}`", "inline": True},
            {"name": "Tx Hash", "value": f"`{self.short_hash()}`", "inline": True},
        ]
        if self.event_data:
            for k, v in list(self.event_data.items())[:3]:
                fields.append({"name": k, "value": f"`{v}`", "inline": True})

        return {
            "embeds": [
                {
                    "title": "📋 Smart Contract Event",
                    "color": 0x9B59B6,
                    "fields": fields,
                    "footer": {
                        "text": f"PharosWatch {'[SIM] ' if self.simulated else ''}• Block #{self.block_number}"
                    },
                }
            ]
        }

    def _deploy_embed(self) -> dict:
        return {
            "embeds": [
                {
                    "title": "🚀 Contract Deployed",
                    "color": 0x2ECC71,
                    "fields": [
                        {"name": "Contract", "value": f"`{self.short_addr(self.contract_address)}`", "inline": True},
                        {"name": "Deployer", "value": f"`{self.short_addr(self.from_address)}`", "inline": True},
                        {"name": "Tx Hash", "value": f"`{self.short_hash()}`", "inline": True},
                    ],
                    "footer": {
                        "text": f"PharosWatch {'[SIM] ' if self.simulated else ''}• Block #{self.block_number}"
                    },
                }
            ]
        }

    def _generic_embed(self) -> dict:
        return {
            "embeds": [
                {
                    "title": f"📡 {self.event_type.value}",
                    "color": 0x95A5A6,
                    "fields": [
                        {"name": "Tx Hash", "value": f"`{self.short_hash()}`", "inline": True},
                        {"name": "Block", "value": f"`#{self.block_number}`", "inline": True},
                    ],
                }
            ]
        }
