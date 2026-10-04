"""MCP client test against a local stdio server (offline)."""
import sys
from pathlib import Path

from codemax.mcp_client.client import MCPClient, ServerConfig

SERVER = str(Path(__file__).parent / "echo_server.py")


def test_discovers_and_calls_tool():
    client = MCPClient([ServerConfig("echo", sys.executable, [SERVER])])
    try:
        tools = client.connect()
        assert client.errors == {}
        assert [t.name for t in tools] == ["echo__echo"]
        assert tools[0].needs_confirm  # no read-only hint -> asks first
        assert tools[0].run({"text": "hi"}) == "echo: hi"
    finally:
        client.close()


def test_bad_server_is_reported_not_fatal():
    client = MCPClient([ServerConfig("bad", "definitely-not-a-command", [])])
    try:
        assert client.connect() == []
        assert "bad" in client.errors
    finally:
        client.close()
