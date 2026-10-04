"""Terminal front end: implements the AgentUI callbacks using rich.

Streams model text live, shows every tool call in a panel, shows a spinner
while the model is thinking, and asks y/n before dangerous tools.
"""
import json

from rich.console import Console
from rich.panel import Panel
from rich.status import Status
from rich.text import Text

MAX_RESULT_LINES = 12


class RichUI:
    def __init__(self, console: Console | None = None):
        self.console = console or Console()
        self._status: Status | None = None
        self._streaming = False  # True while we are mid-way through printing model text

    # --- model output ---------------------------------------------------
    def on_thinking(self, active: bool) -> None:
        if active:
            self._status = self.console.status("[cyan]Thinking...", spinner="dots")
            self._status.start()
        else:
            if self._status:
                self._status.stop()
                self._status = None
            if self._streaming:  # finish the streamed line
                self.console.print()
                self._streaming = False

    def on_token(self, text: str) -> None:
        # First token arrives: stop the spinner so it doesn't fight with the text.
        if self._status:
            self._status.stop()
            self._status = None
        self._streaming = True
        self.console.print(text, end="", markup=False, highlight=False)

    # --- tool calls -----------------------------------------------------
    def _format_args(self, args: dict) -> Text:
        return Text(json.dumps(args, indent=2, ensure_ascii=False))

    def confirm_tool(self, name: str, args: dict) -> bool:
        self.console.print(Panel(self._format_args(args), title=f"[yellow]Tool request: {name}",
                                 border_style="yellow"))
        answer = self.console.input("[yellow]Run this? [y/N] [/yellow]").strip().lower()
        return answer in ("y", "yes")

    def on_tool_start(self, name: str, args: dict) -> None:
        self.console.print(Panel(self._format_args(args), title=f"[green]Running: {name}",
                                 border_style="green"))

    def on_tool_result(self, name: str, result: str) -> None:
        lines = result.splitlines() or [""]
        shown = "\n".join(lines[:MAX_RESULT_LINES])
        if len(lines) > MAX_RESULT_LINES:
            shown += f"\n... ({len(lines) - MAX_RESULT_LINES} more lines)"
        style = "red" if result.startswith("ERROR") or result == "denied by user" else "dim"
        self.console.print(Panel(Text(shown), title=f"Result: {name}", border_style=style))

    def on_notice(self, text: str) -> None:
        self.console.print(f"[bold red]{text}[/bold red]")
