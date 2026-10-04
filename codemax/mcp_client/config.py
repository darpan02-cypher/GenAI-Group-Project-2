"""Which MCP servers CodeMax starts. The RAG server is added in Step 4."""
import os

from .client import ServerConfig


def default_servers(workdir: str) -> list[ServerConfig]:
    servers = [
        # Official filesystem server, limited to the project directory.
        ServerConfig("filesystem", "npx",
                     ["-y", "@modelcontextprotocol/server-filesystem", workdir]),
        # Context7: up-to-date library documentation lookup.
        ServerConfig("context7", "npx", ["-y", "@upstash/context7-mcp"],
                     env=_context7_env()),
    ]
    return servers


def _context7_env() -> dict[str, str]:
    # Stdio servers get a minimal environment, so pass PATH (for node) explicitly.
    env = {"PATH": os.environ.get("PATH", ""), "HOME": os.environ.get("HOME", "")}
    if os.getenv("CONTEXT7_API_KEY"):  # optional: raises rate limits
        env["CONTEXT7_API_KEY"] = os.environ["CONTEXT7_API_KEY"]
    return env
