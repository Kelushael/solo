#!/usr/bin/env bash
set -euo pipefail
APP_DIR="$HOME/.solo-domain/app"
VENV_DIR="$HOME/.solo-domain/venv"
ENV_FILE="$HOME/.solo-domain/.env"
GPU_BASE="${GPU_SOLO_BASE:-http://108.181.162.206:8787}"
PORT="${DOMAIN_PORT:-8080}"
echo "1PA domain gateway install"
echo "GPU brain: $GPU_BASE"
apt update
apt install -y git curl python3 python3-pip python3-venv python3-full
mkdir -p "$HOME/.solo-domain"
if [ -d "$APP_DIR/.git" ]; then cd "$APP_DIR" && git pull --ff-only || true; else rm -rf "$APP_DIR" && git clone https://github.com/Kelushael/solo.git "$APP_DIR"; fi
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/python" -m pip install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements.txt"
cat > "$ENV_FILE" <<EOF
GPU_SOLO_BASE=$GPU_BASE
DOMAIN_HOST=0.0.0.0
DOMAIN_PORT=$PORT
EOF
cat > "$HOME/onepa-domain-start" <<EOF
#!/usr/bin/env bash
cd "$APP_DIR"
"$VENV_DIR/bin/python" domain_gateway.py
EOF
chmod +x "$HOME/onepa-domain-start"
echo "Done. Run: ~/onepa-domain-start"
echo "Open: http://SERVER_IP:$PORT"
