"""The agentic loop: reason -> act -> observe -> repeat.

The loop knows nothing about terminals or specific LLMs. It talks to the
outside world through three things passed in by the caller:
  - provider: an LLMProvider (any backend)
  - tools:    a list of Tool objects (built-in now, MCP later)
  - ui:       an object with the callbacks defined in AgentUI below
"""
import os
import re
import time
from dataclasses import dataclass
from typing import Protocol

from langchain_core.messages import (
    AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage,
)

from codemax.providers.base import LLMProvider
from codemax.tools.base import Tool

SYSTEM_PROMPT = """You are CodeMax, an autonomous coding assistant working in the user's \
project directory. Complete the user's task by using your tools: read files before \
editing them, make changes with edit_file/write_file, and verify your work (for example \
by running tests with run_shell). Work step by step. When the task is finished, reply \
with a short summary and no tool calls.

Working directory: {cwd}
Tools from MCP servers (names like filesystem__*) require ABSOLUTE paths, so build them \
from the working directory above. Built-in tools accept relative paths."""

PROVIDER_RETRY_NUDGE = ("Your last response could not be processed ({error}). Try again, "
                        "and make sure any tool call arguments are valid JSON.")

MAX_RATE_LIMIT_WAIT = 30  # seconds; a longer wait (e.g. a daily token cap) is not worth sleeping on


def rate_limit_wait(error: Exception) -> float | None:
    """If the error is a rate limit, return how many seconds to wait, else None.

    Groq's message says e.g. 'Please try again in 6.5s' or '... in 1m2.3s'.
    """
    text = str(error)
    if "rate limit" not in text.lower() and "429" not in text:
        return None
    m = re.search(r"try again in (?:(\d+)m)?(?:(\d+(?:\.\d+)?)(ms|s))", text)
    if not m:
        return 10.0
    minutes, secs, unit = m.groups()
    wait = float(secs) / (1000 if unit == "ms" else 1) + 60 * int(minutes or 0)
    return wait + 1


DENIED_MESSAGE = "The user denied this tool call. Do not retry it; choose another approach or ask."


class AgentUI(Protocol):
    """What the loop needs from a front end (the CLI implements this)."""
    def on_token(self, text: str) -> None: ...
    def on_thinking(self, active: bool) -> None: ...
    def confirm_tool(self, name: str, args: dict) -> bool: ...
    def on_tool_start(self, name: str, args: dict) -> None: ...
    def on_tool_result(self, name: str, result: str) -> None: ...
    def on_notice(self, text: str) -> None: ...


@dataclass
class AgentConfig:
    max_iterations: int = 15   # guard against endless loops
    provider_retries: int = 2   # extra attempts when the LLM call itself fails
    auto_execute: bool = False  # False = confirm-before-execute mode


class Agent:
    def __init__(self, provider: LLMProvider, tools: list[Tool], ui: AgentUI,
                 config: AgentConfig | None = None):
        self.provider = provider
        self.tools = {t.name: t for t in tools}
        self.ui = ui
        self.config = config or AgentConfig()
        self.messages: list[BaseMessage] = [
            SystemMessage(SYSTEM_PROMPT.format(cwd=os.getcwd()))]

    def run(self, task: str) -> str:
        """Run one task to completion. Returns the model's final answer."""
        self.messages.append(HumanMessage(task))
        specs = [t.to_openai_schema() for t in self.tools.values()]

        for _ in range(self.config.max_iterations):
            # REASON: ask the model what to do next
            reply = self._ask_model(specs)
            if reply is None:
                return "Stopped: the model call kept failing."
            self.messages.append(reply)

            # STOP: no tool calls means the model considers the task done
            if not reply.tool_calls:
                return reply.content if isinstance(reply.content, str) else ""

            # ACT + OBSERVE: run each requested tool, feed results back
            for call in reply.tool_calls:
                result = self._execute(call["name"], call["args"])
                self.messages.append(ToolMessage(result, tool_call_id=call["id"]))

        self.ui.on_notice(f"Stopped: reached max iterations ({self.config.max_iterations}).")
        return "Stopped: max iterations reached."

    def _ask_model(self, specs: list[dict]) -> AIMessage | None:
        """Call the LLM; on failure (e.g. malformed tool-call JSON) retry with a nudge."""
        for attempt in range(self.config.provider_retries + 1):
            self.ui.on_thinking(True)
            try:
                return self.provider.chat(self.messages, specs, self.ui.on_token)
            except Exception as e:
                if attempt == self.config.provider_retries:
                    self.ui.on_notice(f"LLM call failed: {type(e).__name__}: {e}")
                    return None
                wait = rate_limit_wait(e)
                if wait is not None and wait > MAX_RATE_LIMIT_WAIT:
                    self.ui.on_notice(
                        f"Rate limit needs ~{wait/60:.0f} min (daily token cap?). Stopping. "
                        "Wait, or switch model/provider (GROQ_MODEL, --provider ollama).")
                    return None
                if wait is not None:  # short rate limit: just wait, the conversation is fine
                    self.ui.on_notice(f"Rate limited; waiting {wait:.0f}s then retrying...")
                    time.sleep(wait)
                    continue
                self.ui.on_notice(f"LLM call failed ({type(e).__name__}); retrying...")
                self.messages.append(HumanMessage(PROVIDER_RETRY_NUDGE.format(error=str(e)[:200])))
            finally:
                self.ui.on_thinking(False)
        return None

    def _execute(self, name: str, args: dict) -> str:
        tool = self.tools.get(name)
        if tool is None:
            return f"ERROR: unknown tool '{name}'. Available: {', '.join(self.tools)}"

        if tool.needs_confirm and not self.config.auto_execute:
            if not self.ui.confirm_tool(name, args):
                self.ui.on_tool_result(name, "denied by user")
                return DENIED_MESSAGE

        self.ui.on_tool_start(name, args)
        result = tool.run(args)
        self.ui.on_tool_result(name, result)
        return result
