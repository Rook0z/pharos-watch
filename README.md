# 🔭 PharosWatch

Real-time **Pharos Network** event tracker — monitors wallet activity and smart contract events, fires Discord alerts via webhook.

Built with Python `asyncio` + WebSockets. Runs in **simulation mode** today with a clean plug-in point for live Pharos data once the API is public.

---

## Features

- 📡 **Real-time event ingestion** via WebSocket (simulated stream until Pharos API is live)
- 💸 **Wallet transfer tracking** — monitor specific addresses for incoming/outgoing transfers
- 📋 **Smart contract event parsing** — watch any contract for on-chain events (Transfer, Swap, Mint, Burn, etc.)
- 🚨 **Large transfer detection** — auto-flags high-value movements
- 🔔 **Discord alerts** — rich embeds with rate limiting + retry logic
- 🔧 **Filter engine** — configurable thresholds and address allowlists
- 📝 **Full logging** — console + rotating log file

---

## Quickstart

```bash
# 1. Clone & install deps
git clone https://github.com/YOUR_USERNAME/pharos-watch
cd pharos-watch
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env — add your DISCORD_WEBHOOK_URL and wallet addresses

# 3. Run (simulation mode by default)
python main.py
```

---

## Configuration

All config lives in `.env`:

| Variable | Description | Default |
|---|---|---|
| `DISCORD_WEBHOOK_URL` | Discord webhook for alerts | *(required)* |
| `TRACKED_WALLETS` | Comma-separated wallet addresses | *(empty = all)* |
| `TRACKED_CONTRACTS` | Comma-separated contract addresses | *(empty = all)* |
| `MIN_TRANSFER_VALUE_ETH` | Minimum value to alert on | `0.01` |
| `SIMULATION_MODE` | Use simulated events | `true` |
| `PHAROS_WS_URL` | Pharos WebSocket endpoint | placeholder |
| `POLL_INTERVAL` | Seconds between simulated events | `5` |

---

## Architecture

```
main.py
  └── PharosTracker
        ├── SimulatedStream (or PharosWebSocketStream)   ← event ingestion
        ├── EventFilter                                   ← rules engine
        └── AlertPipeline                                 ← Discord webhook sender
```

### Switching to live Pharos data

1. Set `SIMULATION_MODE=false` in `.env`
2. Set `PHAROS_WS_URL` to the real Pharos WebSocket endpoint
3. Update `PharosWebSocketStream._parse()` in `src/stream.py` to match the actual Pharos message schema

---

## Project Structure

```
pharos-watch/
├── main.py               # Entry point
├── requirements.txt
├── .env.example
├── src/
│   ├── tracker.py        # Orchestrator
│   ├── stream.py         # Event ingestion (simulated + real WS)
│   ├── models.py         # PharosEvent dataclass + Discord embed builder
│   ├── alerts.py         # Discord webhook sender with rate limiting
│   ├── filters.py        # Alert filter/rules engine
│   ├── config.py         # Config loader (.env)
│   └── logger.py         # Logging setup
└── logs/                 # Auto-created at runtime
```

---

## Discord Alert Examples

**Wallet Transfer**
> 💸 Wallet Transfer | From: `0xabc...1234` → To: `0xdef...5678` | Amount: `1.2500 ETH`

**Large Transfer**
> 🚨 Large Transfer Detected | From: `0xabc...` → To: `0xdef...` | Amount: `250.00 ETH`

**Contract Event**
> 📋 Smart Contract Event | Contract: `0x123...` | Event: `Swap` | token_in: `USDC` | token_out: `ETH`

**Contract Deploy**
> 🚀 Contract Deployed | Contract: `0xnew...` | Deployer: `0xdev...`

---


## License

MIT
