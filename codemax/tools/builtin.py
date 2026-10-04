"""Built-in tools: read/write/edit files, run shell commands, search code.

Each function is plain Python that returns a string. The Tool wrappers at the
bottom describe them to the LLM (name, description, JSON schema).
"""
import os
import re
import subprocess
from pathlib import Path

from .base import Tool

MAX_OUTPUT_CHARS = 8000  # keep tool results small so we don't flood the LLM context
SHELL_TIMEOUT_SECONDS = 60
SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", "chroma_db"}


def _truncate(text: str) -> str:
    if len(text) <= MAX_OUTPUT_CHARS:
        return text
    return text[:MAX_OUTPUT_CHARS] + f"\n... [truncated, {len(text) - MAX_OUTPUT_CHARS} more chars]"


def read_file(path: str) -> str:
    return _truncate(Path(path).read_text())


def write_file(path: str, content: str) -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return f"Wrote {len(content)} chars to {path}"


def edit_file(path: str, old_text: str, new_text: str) -> str:
    """Replace one exact piece of text. Fails if it is missing or ambiguous."""
    p = Path(path)
    original = p.read_text()
    count = original.count(old_text)
    if count == 0:
        raise ValueError("old_text not found in file")
    if count > 1:
        raise ValueError(f"old_text appears {count} times; include more surrounding text")
    p.write_text(original.replace(old_text, new_text))
    return f"Edited {path}"


def run_shell(command: str) -> str:
    result = subprocess.run(
        command, shell=True, capture_output=True, text=True, timeout=SHELL_TIMEOUT_SECONDS
    )
    out = f"exit code: {result.returncode}\n"
    if result.stdout:
        out += f"stdout:\n{result.stdout}"
    if result.stderr:
        out += f"stderr:\n{result.stderr}"
    return _truncate(out)


def search_code(pattern: str, directory: str = ".") -> str:
    """Regex search over text files; returns 'path:line: text' matches."""
    regex = re.compile(pattern)
    matches = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            fp = Path(root) / name
            try:
                lines = fp.read_text().splitlines()
            except (UnicodeDecodeError, OSError):
                continue  # binary or unreadable file
            for i, line in enumerate(lines, 1):
                if regex.search(line):
                    matches.append(f"{fp}:{i}: {line.strip()}")
                    if len(matches) >= 100:
                        return _truncate("\n".join(matches) + "\n... [100 match limit]")
    return _truncate("\n".join(matches)) if matches else "No matches."


def _schema(**props: str) -> dict:
    """Build a JSON schema where every property is a required string."""
    return {
        "type": "object",
        "properties": {k: {"type": "string", "description": v} for k, v in props.items()},
        "required": list(props),
    }


def builtin_tools() -> list[Tool]:
    return [
        Tool("read_file", "Read a text file and return its contents.",
             _schema(path="File path"), read_file),
        Tool("search_code", "Regex-search files under a directory. Returns path:line: text.",
             {**_schema(pattern="Regex pattern", directory="Directory to search"),
              "required": ["pattern"]}, search_code),
        Tool("write_file", "Create or overwrite a file with the given content.",
             _schema(path="File path", content="Full file content"), write_file,
             needs_confirm=True),
        Tool("edit_file", "Replace one exact occurrence of old_text with new_text in a file.",
             _schema(path="File path", old_text="Exact text to replace",
                     new_text="Replacement text"), edit_file, needs_confirm=True),
        Tool("run_shell", "Run a shell command and return exit code, stdout and stderr.",
             _schema(command="Shell command"), run_shell, needs_confirm=True),
    ]
