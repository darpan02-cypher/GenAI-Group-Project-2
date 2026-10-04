"""Tool definition shared by built-in tools and (later) MCP tools.

A Tool is just: a name, a description, a JSON-schema for its arguments, and a
function to run. Keeping it this simple means MCP tools (which arrive as
name + description + JSON schema) can be wrapped in the same class later.
"""
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict[str, Any]  # JSON schema for the arguments
    func: Callable[..., str]    # does the work, always returns a string
    # Dangerous tools (write, edit, shell) ask for confirmation in confirm mode.
    # Read-only tools run without asking.
    needs_confirm: bool = False

    def to_openai_schema(self) -> dict[str, Any]:
        """Format the LLM understands (OpenAI-style function spec).

        LangChain's bind_tools accepts this format for both Groq and Ollama.
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def run(self, args: dict[str, Any]) -> str:
        """Run the tool; turn any exception into text so the LLM can react to it."""
        try:
            return str(self.func(**args))
        except Exception as e:  # observe errors instead of crashing the loop
            return f"ERROR: {type(e).__name__}: {e}"
