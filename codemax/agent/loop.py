"""The agentic loop: reason -> act -> observe -> repeat.

The loop knows nothing about terminals or specific LLMs. It talks to the
outside world through three things passed in by the caller:
  - provider: an LLMProvider (any backend)
  - tools:    a list of Tool objects (built-in now, MCP later)
  - ui:       an object with the callbacks defined in AgentUI below
"""
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
with a short summary and no tool calls."""

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
    auto_execute: bool = False  # False = confirm-before-execute mode


class Agent:
    def __init__(self, provider: LLMProvider, tools: list[Tool], ui: AgentUI,
                 config: AgentConfig | None = None):
        self.provider = provider
        self.tools = {t.name: t for t in tools}
        self.ui = ui
        self.config = config or AgentConfig()
        self.messages: list[BaseMessage] = [SystemMessage(SYSTEM_PROMPT)]

    def run(self, task: str) -> str:
        """Run one task to completion. Returns the model's final answer."""
        self.messages.append(HumanMessage(task))
        specs = [t.to_openai_schema() for t in self.tools.values()]

        for _ in range(self.config.max_iterations):
            # REASON: ask the model what to do next
            self.ui.on_thinking(True)
            try:
                reply: AIMessage = self.provider.chat(self.messages, specs, self.ui.on_token)
            finally:
                self.ui.on_thinking(False)
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
