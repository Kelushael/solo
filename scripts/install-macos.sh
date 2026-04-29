#!/usr/bin/env bash
set -e

echo "🍎 Installing Solo on macOS"

brew install python3 || true

if ! command -v ollama &> /dev/null; then
  curl -fsSL https://ollama.com/install.sh | sh
fi

ollama pull deepseek-coder:6.7b || true

mkdir -p ~/.solo
cd ~/.solo

git clone https://github.com/Kelushael/solo.git app || true
cd app

pip3 install -r requirements.txt

cat > ~/.solo/.env <<EOF
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

echo "alias solo-start='cd ~/.solo/app && python3 solo_agent.py'" >> ~/.zshrc

echo "✅ Done. Restart terminal and run: solo-start"
