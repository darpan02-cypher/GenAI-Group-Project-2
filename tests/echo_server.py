"""Tiny MCP server used only by tests (no network, no npx)."""
from mcp.server.mcpserver import MCPServer

app = MCPServer("echo")


@app.tool()
def echo(text: str) -> str:
    """Return the text back."""
    return f"echo: {text}"


if __name__ == "__main__":
    app.run()
