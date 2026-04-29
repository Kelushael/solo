#!/usr/bin/env python3
import os
from pathlib import Path
import requests
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

HOME = Path.home()
SOLO_DIR = HOME / ".solo"
ENV_FILE = SOLO_DIR / ".env"
NOTES_DIR = SOLO_DIR / "notes"
PROPOSALS_DIR = SOLO_DIR / "proposals"
API = "http://localhost:8787"

NOTES_DIR.mkdir(parents=True, exist_ok=True)
PROPOSALS_DIR.mkdir(parents=True, exist_ok=True)
load_dotenv(ENV_FILE)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-coder:6.7b")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "change-me")
console = Console()

ART = r'''
██╗██████╗  █████╗ 
██║██╔══██╗██╔══██╗
██║██████╔╝███████║
██║██╔═══╝ ██╔══██║
██║██║     ██║  ██║
╚═╝╚═╝     ╚═╝  ╚═╝

        1PA
'''

SYSTEM = """
You are Solo, a local terminal trading assistant for 1PA PRO v6.
1PA PRO v6 automated trading bot context:
- Connects TradingView alerts to Tradovate and NinjaTrader 8 workflows.
- Instruments: NQ, MNQ, GC, MGC.
- Includes Big Run Mode, Adaptive Stop, Early Warn exits, Divergence signals, Vol Reversal signals, and Daily P&L limits.
- A+ grade and score threshold rules matter.
- Treat live trading as high risk and never guarantee profit.
- Help the user reason about signals, risk, configuration, and strategy.
- Be practical, direct, and execution-aware.
"""

HELP = """
Commands:
  help        show this menu
  status      check local Solo engine
  env         show ~/.solo/.env
  note TEXT   save a note
  proposal X  draft an enhancement proposal
  paperlong   send paper long test signal
  papershort  send paper short test signal
  exitpaper   send paper exit test signal
  quit        exit chat

Anything else chats with Solo.
"""

def ask_llm(text):
    try:
        r = requests.post(OLLAMA_URL, json={"model": OLLAMA_MODEL, "prompt": SYSTEM + "\n\nUser: " + text + "\nSolo:", "stream": False}, timeout=90)
        r.raise_for_status()
        return r.json().get("response", "") or "Solo returned no text."
    except Exception as exc:
        return f"Solo brain unavailable: {exc}"

def status():
    try:
        r = requests.get(API + "/", timeout=5)
        console.print_json(data=r.json())
    except Exception as exc:
        console.print(f"[yellow]Solo engine not running:[/yellow] {exc}")
        console.print("Start the engine in another terminal with: [bold]solo-start[/bold]")

def signal(action, sentiment, score):
    payload = {"ticker": "NQ1!", "action": action, "sentiment": sentiment, "score": score, "secret": WEBHOOK_SECRET}
    try:
        r = requests.post(API + "/webhook", json=payload, timeout=90)
        console.print_json(data=r.json())
    except Exception as exc:
        console.print(f"[red]Signal failed:[/red] {exc}")

def proposal(idea):
    text = ask_llm("Create a safe Solo enhancement proposal for: " + idea + ". Include purpose, files affected, steps, and test command.")
    path = PROPOSALS_DIR / "latest.md"
    path.write_text(text, encoding="utf-8")
    console.print(Panel(text, title="1PA Enhancement Proposal", border_style="yellow"))
    console.print(f"Saved: {path}")

def main():
    console.print(Panel(f"[black on yellow]{ART}[/black on yellow]", border_style="yellow"))
    console.print("Type [bold yellow]help[/bold yellow] for commands. Normal text chats with Solo.\n")
    while True:
        try:
            text = Prompt.ask("[black on yellow] solo [/black on yellow]").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\nSolo offline.")
            break
        if not text:
            continue
        if text in {"quit", "exit"}:
            break
        if text == "help":
            console.print(HELP)
        elif text == "status":
            status()
        elif text == "env":
            console.print(ENV_FILE.read_text(errors="replace") if ENV_FILE.exists() else "No ~/.solo/.env found.")
        elif text.startswith("note "):
            with (NOTES_DIR / "solo_notes.md").open("a", encoding="utf-8") as f:
                f.write("- " + text[5:] + "\n")
            console.print("[green]note saved[/green]")
        elif text.startswith("proposal "):
            proposal(text[9:])
        elif text == "paperlong":
            signal("buy", "long", 82)
        elif text == "papershort":
            signal("sell", "short", 82)
        elif text == "exitpaper":
            signal("exit", "flat", 100)
        else:
            console.print(Panel(ask_llm(text), title="Solo", border_style="yellow"))

if __name__ == "__main__":
    main()
