#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$HOME/.solo/app"
VENV_DIR="$HOME/.solo/venv"
ENV_FILE="$HOME/.solo/.env"
REPO_URL="https://github.com/Kelushael/solo.git"
SHELL_NAME="$(basename "${SHELL:-zsh}")"
PROFILE_FILE="$HOME/.zshrc"

if [ "$SHELL_NAME" = "bash" ]; then
  PROFILE_FILE="$HOME/.bash_profile"
fi

printf '\n🍎 Solo macOS Installer\n'
printf 'This can be pasted directly into Terminal. It installs into ~/.solo and avoids system Python.\n\n'

if [ "$(id -u)" = "0" ]; then
  printf '⚠️  You are running as root. Solo is meant to install as your normal macOS user.\n'
  printf 'Continuing anyway, but ~/.solo will belong to root. Press Ctrl+C to stop if that is not what you want.\n'
  sleep 3
fi

need_cmd() {
  command -v "$1" >/dev/null 2>&1
}

ensure_xcode_tools() {
  if ! xcode-select -p >/dev/null 2>&1; then
    printf '\n🧰 Installing Apple Command Line Tools. macOS may open a prompt.\n'
    xcode-select --install || true
    printf 'After Command Line Tools finishes, rerun this installer if git is still missing.\n'
  fi
}

ensure_homebrew() {
  if ! need_cmd brew; then
    printf '\n🍺 Homebrew not found. Installing Homebrew. You may be asked for your macOS password.\n'
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    if [ -x /opt/homebrew/bin/brew ]; then
      eval "$(/opt/homebrew/bin/brew shellenv)"
      grep -q 'brew shellenv' "$PROFILE_FILE" 2>/dev/null || echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> "$PROFILE_FILE"
    elif [ -x /usr/local/bin/brew ]; then
      eval "$(/usr/local/bin/brew shellenv)"
      grep -q 'brew shellenv' "$PROFILE_FILE" 2>/dev/null || echo 'eval "$(/usr/local/bin/brew shellenv)"' >> "$PROFILE_FILE"
    fi
  fi
}

ensure_xcode_tools
ensure_homebrew

if ! need_cmd git; then
  printf '\n📦 Installing git...\n'
  brew install git
fi

if ! need_cmd python3; then
  printf '\n🐍 Installing python3...\n'
  brew install python
fi

if ! need_cmd ollama; then
  printf '\n🦙 Installing Ollama with Homebrew...\n'
  brew install ollama || brew install --cask ollama || true
fi

if need_cmd ollama; then
  printf '\n🧠 Pulling DeepSeek 7B-class model...\n'
  ollama pull deepseek-coder:6.7b || true
else
  printf '\n⚠️  Ollama was not found after install attempt. Install Ollama manually later if needed.\n'
fi

mkdir -p "$HOME/.solo"

if [ -d "$APP_DIR/.git" ]; then
  printf '\n🔄 Solo app already exists. Updating repo...\n'
  cd "$APP_DIR"
  git pull --ff-only || true
else
  printf '\n📦 Cloning Solo app...\n'
  rm -rf "$APP_DIR"
  git clone "$REPO_URL" "$APP_DIR"
fi

printf '\n🐍 Creating isolated Python virtual environment...\n'
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
mkdir -p "$HOME/.solo/logs"
tail -f "$HOME/.solo/logs/solo.jsonl"
EOC
chmod +x "$HOME/solo-logs"

mkdir -p "$HOME/bin"
ln -sf "$HOME/solo-start" "$HOME/bin/solo-start"
ln -sf "$HOME/solo-logs" "$HOME/bin/solo-logs"

if ! echo "$PATH" | grep -q "$HOME/bin"; then
  echo 'export PATH="$HOME/bin:$PATH"' >> "$PROFILE_FILE"
fi

printf '\n✅ Solo installed on macOS.\n'
printf 'Run now with: ~/solo-start\n'
printf 'Or open a new Terminal and run: solo-start\n'
printf 'Logs: ~/solo-logs\n'
printf 'Config: ~/.solo/.env\n\n'
