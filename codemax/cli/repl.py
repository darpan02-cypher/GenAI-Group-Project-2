"""Interactive REPL: banner, prompt, slash commands, runs the agent per task."""
import argparse

from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from rich.console import Console
from rich.panel import Panel

from codemax.agent.loop import Agent, AgentConfig
from codemax.cli.ui import RichUI
from codemax.providers.factory import make_provider
from codemax.tools.builtin import builtin_tools

BANNER = "[bold cyan]CodeMax[/bold cyan] - autonomous coding assistant"
HELP = """[bold]Commands[/bold]
  /auto      switch to auto-execute (tools run without asking)
  /confirm   switch to confirm-before-execute (default)
  /help      show this help
  /exit      quit"""


def main() -> None:
    parser = argparse.ArgumentParser(prog="codemax")
    parser.add_argument("--provider", choices=["groq", "ollama"], help="LLM backend")
    parser.add_argument("--auto", action="store_true", help="start in auto-execute mode")
    args = parser.parse_args()

    console = Console()
    try:
        provider = make_provider(args.provider)
    except Exception as e:
        console.print(f"[red]Could not start provider: {e}[/red]")
        raise SystemExit(1)

    config = AgentConfig(auto_execute=args.auto)
    agent = Agent(provider, builtin_tools(), RichUI(console), config)

    def mode() -> str:
        return "auto-execute" if config.auto_execute else "confirm"

    console.print(Panel(f"{BANNER}\nprovider: {provider.name} | mode: {mode()}\n"
                        "Type a task, or /help.", border_style="cyan"))

    session = PromptSession(history=InMemoryHistory())
    while True:
        try:
            text = session.prompt(f"codemax [{mode()}]> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not text:
            continue
        if text in ("/exit", "/quit"):
            break
        if text == "/help":
            console.print(HELP)
        elif text == "/auto":
            config.auto_execute = True
            console.print("[yellow]Auto-execute ON: tools run without asking.[/yellow]")
        elif text == "/confirm":
            config.auto_execute = False
            console.print("[green]Confirm mode ON.[/green]")
        else:
            try:
                agent.run(text)
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted.[/yellow]")
            except Exception as e:  # provider/network errors: report, keep the REPL alive
                console.print(f"[red]Error: {type(e).__name__}: {e}[/red]")
    console.print("Bye.")


if __name__ == "__main__":
    main()
