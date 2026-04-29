#!/usr/bin/env bash
set -e

APP_DIR="$HOME/.solo/app"
VENV_DIR="$HOME/.solo/venv"
ENV_FILE="$HOME/.solo/.env"

printf '\n🔥 Installing Solo on Debian/Ubuntu\n'

sudo apt update
sudo apt install -y git curl python3 python3-pip python3-venv python3-full

# Install Ollama if not present
if ! command -v ollama >/dev/null 2>&1; then
  curl -fsSL https://ollama.com/install.sh | sh
fi

ollama pull deepseek-coder:6.7b || true

mkdir -p "$HOME/.solo"

if [ -d "$APP_DIR/.git" ]; then
  printf '\n🔄 Solo app already exists. Updating repo...\n'
  cd "$APP_DIR"
  git pull --ff-only || true
else
  printf '\n📦 Cloning Solo app...\n'
  rm -rf "$APP_DIR"
  git clone https://github.com/Kelushael/solo.git "$APP_DIR"
fi

printf '\n🐍 Creating Python virtual environment...\n'
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/python" -m pip install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements.txt"

if [ ! -f "$ENV_FILE" ]; then
  cat > "$ENV_FILE" <<EOF
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
EOF
fi

cat > "$HOME/solo-start" <<EOC
#!/usr/bin/env bash
cd "$APP_DIR"
"$VENV_DIR/bin/python" solo_agent.py
EOC
chmod +x "$HOME/solo-start"

cat > "$HOME/solo-logs" <<EOC
#!/usr/bin/env bash
tail -f "$HOME/.solo/logs/solo.jsonl"
EOC
chmod +x "$HOME/solo-logs"

printf '\n✅ Solo installed. Run: ~/solo-start\n'
printf '📜 Logs: ~/solo-logs\n'
printf '⚙️ Config: ~/.solo/.env\n'
