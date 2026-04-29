# Solo

Local-first webhook receiver and rule gate for TradingView alerts.

Default mode is safe logging mode. Live forwarding requires `SOLO_LIVE=1` and a configured `TRADERSPOST_WEBHOOK_URL`.

## Install

### Debian or Ubuntu

```bash
curl -fsSL https://raw.githubusercontent.com/Kelushael/solo/main/scripts/install-debian.sh | bash
```

### macOS

```bash
curl -fsSL https://raw.githubusercontent.com/Kelushael/solo/main/scripts/install-macos.sh | bash
```

### Windows PowerShell remote installer

```powershell
iwr -useb https://raw.githubusercontent.com/Kelushael/solo/main/scripts/install-windows.ps1 | iex
```

The Windows installer sets up SSH key login for:

```text
administrator@108.181.162.206
```

Then it creates a `solo` command for future SSH login.

## Commands

```bash
solo-start
solo-stop
solo-status
solo-logs
```

## Config

Edit:

```bash
~/.solo/.env
```

Example:

```env
SOLO_HOST=0.0.0.0
SOLO_PORT=8787
SOLO_LIVE=0
TRADERSPOST_WEBHOOK_URL=
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=deepseek-coder:6.7b
MIN_SCORE=75
MAX_CONTRACTS=2
DAILY_EXIT_EST=16:45
WEBHOOK_SECRET=change-me
```

## TradingView webhook body

```json
{"ticker":"{{ticker}}","action":"buy","sentiment":"long","score":82,"secret":"change-me"}
```

Endpoint:

```text
POST http://YOUR_SERVER_IP:8787/webhook
```

Futures trading is risky. This software is automation infrastructure, not a profit guarantee.
