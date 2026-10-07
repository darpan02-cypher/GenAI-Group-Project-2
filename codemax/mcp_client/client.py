"""MCP client: connects to MCP servers and exposes their tools as Tool objects.

The MCP SDK is async, but our agent loop is plain synchronous code. So we run
one asyncio event loop in a background thread and hand it work with
run_coroutine_threadsafe. Callers just use ordinary blocking methods.

Each server is a subprocess we talk to over stdio. Its tools are discovered at
runtime (list_tools) - nothing about them is hard-coded here.
"""
import asyncio
import threading
from contextlib import AsyncExitStack
from dataclasses import dataclass, field

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from codemax.tools.base import Tool

MAX_DESCRIPTION_CHARS = 400  # long descriptions eat the LLM's token budget on every call
CONNECT_TIMEOUT_SECONDS = 90  # first npx run may need to download the server


@dataclass
class ServerConfig:
    name: str                        # short label, used to prefix tool names
    command: str                     # e.g. "npx"
    args: list[str]
    env: dict[str, str] = field(default_factory=dict)


class MCPClient:
    def __init__(self, servers: list[ServerConfig]):
        self._configs = servers
        self._sessions: dict[str, ClientSession] = {}
        self._tool_origin: dict[str, tuple[str, str]] = {}  # our name -> (server, real name)
        self.errors: dict[str, str] = {}                    # server name -> why it failed
        self._stack = AsyncExitStack()
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()

    # --- helpers --------------------------------------------------------
    def _run(self, coro, timeout: float | None = None):
        """Run a coroutine on the background loop and wait for its result."""
        return asyncio.run_coroutine_threadsafe(coro, self._loop).result(timeout)

    # --- connecting -----------------------------------------------------
    def connect(self) -> list[Tool]:
        """Start every server, list its tools, return them all as Tool objects."""
        tools: list[Tool] = []
        for cfg in self._configs:
            try:
                tools += self._run(self._connect_one(cfg), CONNECT_TIMEOUT_SECONDS)
            except Exception as e:  # one broken server must not stop the others
                self.errors[cfg.name] = f"{type(e).__name__}: {e}"
        return tools

    async def _connect_one(self, cfg: ServerConfig) -> list[Tool]:
        params = StdioServerParameters(command=cfg.command, args=cfg.args, env=cfg.env or None)
        read, write = await self._stack.enter_async_context(stdio_client(params))
        session = await self._stack.enter_async_context(ClientSession(read, write))
        await session.initialize()
        self._sessions[cfg.name] = session

        listing = await session.list_tools()
        tools = []
        for t in listing.tools:
            our_name = f"{cfg.name}__{t.name}"  # prefix avoids name clashes between servers
            self._tool_origin[our_name] = (cfg.name, t.name)
            # Tools the server marks read-only run freely; anything else asks first.
            read_only = bool(t.annotations and t.annotations.read_only_hint)
            tools.append(Tool(
                name=our_name,
                description=f"[{cfg.name}] {(t.description or t.name)[:MAX_DESCRIPTION_CHARS]}",
                parameters=t.input_schema or {"type": "object", "properties": {}},
                func=lambda _n=our_name, **kw: self.call_tool(_n, kw),
                needs_confirm=not read_only,
            ))
        return tools

    # --- calling --------------------------------------------------------
    def call_tool(self, name: str, args: dict) -> str:
        server, real_name = self._tool_origin[name]
        result = self._run(self._sessions[server].call_tool(real_name, args))
        text = "\n".join(c.text for c in result.content if getattr(c, "text", None))
        if result.is_error:
            raise RuntimeError(text or "MCP tool returned an error")
        return text

    def server_names(self) -> list[str]:
        return list(self._sessions)

    def close(self) -> None:
        try:
            self._run(self._stack.aclose(), 10)
        except Exception:
            pass
        self._loop.call_soon_threadsafe(self._loop.stop)
