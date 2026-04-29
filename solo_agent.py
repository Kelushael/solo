#!/usr/bin/env python3
import json
import os
import time
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

load_dotenv(os.path.expanduser("~/.solo/.env"))

SOLO_HOST = os.getenv("SOLO_HOST", "0.0.0.0")
SOLO_PORT = int(os.getenv("SOLO_PORT", "8787"))
SOLO_LIVE = os.getenv("SOLO_LIVE", "0") == "1"
TRADERSPOST_WEBHOOK_URL = os.getenv("TRADERSPOST_WEBHOOK_URL", "")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-coder:6.7b")
MIN_SCORE = int(os.getenv("MIN_SCORE", "75"))
MAX_CONTRACTS = int(os.getenv("MAX_CONTRACTS", "2"))
DAILY_EXIT_EST = os.getenv("DAILY_EXIT_EST", "16:45")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "change-me")
LOG_DIR = os.path.expanduser(os.getenv("SOLO_LOG_DIR", "~/.solo/logs"))
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "solo.jsonl")

app = FastAPI(title="Solo DeepSeek Webhook Agent")
STATE = {"positions": {}, "last_signal": None}

SYSTEM_CONTEXT = """
You are Solo, the 1PA PRO v6 terminal/cloud trading assistant.
Context:
- Connects TradingView alerts to Tradovate, NinjaTrader 8, or webhook execution workflows.
- Instruments: NQ, MNQ, GC, MGC.
- Includes Big Run Mode, Adaptive Stop, Early Warn exits, Divergence signals, Vol Reversal signals, and Daily P&L limits.
- A+ grade and score threshold rules matter.
- Treat live trading as high risk. Never guarantee profit.
- Help with signal reasoning, risk rules, configuration, and system operation.
"""

class Signal(BaseModel):
    ticker: str = "NQ1!"
    action: str
    sentiment: str = ""
    score: int = 0
    secret: str = ""
    contracts: int = 1


def log_event(event, **data):
    row = {"timestamp_local": datetime.now().isoformat(timespec="seconds"), "event": event, **data}
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps(row, ensure_ascii=False), flush=True)


def ask_llm(prompt):
    try:
        r = requests.post(OLLAMA_URL, json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}, timeout=90)
        r.raise_for_status()
        return r.json().get("response", "")
    except Exception as e:
        return f"[DeepSeek Error: {e}]"


def after_daily_exit():
    hh, mm = DAILY_EXIT_EST.split(":")
    now = datetime.now(ZoneInfo("America/New_York")).time()
    return now >= dtime(int(hh), int(mm))


def is_weekend():
    return datetime.now(ZoneInfo("America/New_York")).weekday() >= 5


def risk_check(sig: Signal):
    action = sig.action.lower().strip()
    open_contracts = sum(p.get("contracts", 0) for p in STATE["positions"].values())
    if sig.secret != WEBHOOK_SECRET:
        return False, "bad webhook secret"
    if action not in {"buy", "sell", "exit"}:
        return False, "unsupported action"
    if action != "exit" and sig.score < MIN_SCORE:
        return False, f"score {sig.score} below minimum {MIN_SCORE}"
    if action != "exit" and is_weekend():
        return False, "weekend entries disabled"
    if action != "exit" and after_daily_exit():
        return False, "after daily exit cutoff"
    if action != "exit" and open_contracts + sig.contracts > MAX_CONTRACTS:
        return False, "max contracts exceeded"
    return True, "passed Solo risk rules"


def make_decision(sig: Signal, approved: bool, reason: str):
    prompt = f"""
{SYSTEM_CONTEXT}
Rules:
- Only take A+ setups with score >= {MIN_SCORE}
- Max {MAX_CONTRACTS} contracts
- Respect stop loss always
- No trades after {DAILY_EXIT_EST} EST
- No weekend holds
Signal JSON:
{sig.model_dump_json()}
Risk gate approved: {approved}
Risk reason: {reason}
Decide one of: ENTER_LONG, ENTER_SHORT, EXIT, SKIP.
Briefly explain why.
"""
    return ask_llm(prompt)


def forward_to_traderspost(sig: Signal):
    payload = {"ticker": sig.ticker, "action": sig.action, "sentiment": sig.sentiment}
    if not SOLO_LIVE:
        return {"forwarded": False, "mode": "paper", "payload": payload}
    if not TRADERSPOST_WEBHOOK_URL:
        return {"forwarded": False, "error": "TRADERSPOST_WEBHOOK_URL missing"}
    r = requests.post(TRADERSPOST_WEBHOOK_URL, json=payload, timeout=20)
    return {"forwarded": True, "status_code": r.status_code, "text": r.text[:500]}


@app.get("/")
def root():
    return {"ok": True, "agent": "Solo", "model": OLLAMA_MODEL, "live": SOLO_LIVE, "last_signal": STATE.get("last_signal")}


@app.get("/logs")
def logs():
    if not os.path.exists(LOG_FILE):
        return PlainTextResponse("")
    with open(LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()[-80:]
    return PlainTextResponse("".join(lines))


@app.post("/chat")
async def chat(request: Request):
    raw = await request.json()
    message = raw.get("message", "")
    if message.strip().lower() == "status":
        return {"reply": json.dumps(root(), indent=2)}
    prompt = f"{SYSTEM_CONTEXT}\nCurrent state:\n{json.dumps(STATE, default=str)}\n\nUser:\n{message}\n\nSolo:"
    reply = ask_llm(prompt)
    log_event("chat", message=message, reply=reply)
    return {"reply": reply}


@app.post("/webhook")
async def webhook(request: Request):
    raw = await request.json()
    sig = Signal(**raw)
    approved, reason = risk_check(sig)
    thought = make_decision(sig, approved, reason)
    forward_result = None
    if approved:
        action = sig.action.lower()
        if action == "exit":
            STATE["positions"].clear()
        else:
            STATE["positions"][f"{sig.ticker}:{action}"] = {"contracts": sig.contracts, "time": time.time()}
        forward_result = forward_to_traderspost(sig)
    STATE["last_signal"] = raw
    log_event("signal_processed", signal=raw, approved=approved, reason=reason, thought=thought, forward_result=forward_result)
    return {"approved": approved, "reason": reason, "thought": thought, "forward_result": forward_result}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=SOLO_HOST, port=SOLO_PORT)
