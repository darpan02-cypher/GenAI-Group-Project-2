"""Provider abstraction: one interface, many LLM backends.

The agent loop only knows about LLMProvider.chat(). To add a provider you
subclass it; nothing else in the codebase changes.
"""
from abc import ABC, abstractmethod
from typing import Callable

from langchain_core.messages import AIMessage, BaseMessage


class LLMProvider(ABC):
    name: str

    @abstractmethod
    def chat(
        self,
        messages: list[BaseMessage],
        tools: list[dict],
        on_token: Callable[[str], None] | None = None,
    ) -> AIMessage:
        """Send the conversation to the model and return its full reply.

        - tools: OpenAI-style tool specs (see Tool.to_openai_schema).
        - on_token: called with each text piece as it streams, so the CLI can
          print live. The returned AIMessage holds the complete text and any
          tool_calls the model asked for.
        """


class LangChainProvider(LLMProvider):
    """Shared streaming logic for any LangChain chat model."""

    def __init__(self, model):
        self._model = model

    def chat(self, messages, tools, on_token=None) -> AIMessage:
        model = self._model.bind_tools(tools) if tools else self._model
        full = None
        for chunk in model.stream(messages):
            if chunk.content and on_token:
                on_token(chunk.content if isinstance(chunk.content, str) else "")
            # Chunks add together: text concatenates, tool-call pieces merge.
            full = chunk if full is None else full + chunk
        if full is None:
            return AIMessage(content="")
        return AIMessage(content=full.content, tool_calls=full.tool_calls)
