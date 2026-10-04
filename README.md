# GenAI-Group-Project-2

**CodeMax** is an autonomous CLI AI coding assistant. It takes a task in plain English, reasons, calls tools (files, shell, MCP servers) and loops until the task is done.

> Status: planning. See [SPEC.md](SPEC.md) and [PLAN.md](PLAN.md).

## Setup
```
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then add your GROQ_API_KEY
```
For local models, install [Ollama](https://ollama.com) and run `ollama pull qwen2.5-coder:7b`.

## Usage
```
python -m codemax                    # Groq, confirm mode
python -m codemax --provider ollama  # local model
python -m codemax --auto             # tools run without asking
```
In the REPL: `/auto`, `/confirm`, `/help`, `/exit`. Tests: `pytest`.

## Configuration
_TODO: env vars (e.g. GROQ_API_KEY), Ollama model, confirm/auto mode._

## MCP servers
1. Filesystem (`@modelcontextprotocol/server-filesystem`)
2. Context7
3. Custom RAG server over the RAGAs docs

## Project layout
See SPEC.md section 5.
