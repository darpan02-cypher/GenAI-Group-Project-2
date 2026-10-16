# GenAI-Group-Project-2

**CodeMax** is an autonomous CLI AI coding assistant. It takes a task in plain English, reasons, calls tools (files, shell, MCP servers) and loops until the task is done.

> Status: all three MCP servers working. See [SPEC.md](SPEC.md) and [PLAN.md](PLAN.md).

## Demo
[Watch the CodeMax demo video](CodeMax_demo.mp4)

<video src="CodeMax_demo.mp4" controls width="720"></video>

## Setup
```
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then add your GROQ_API_KEY
```
For local models, install [Ollama](https://ollama.com) and run `ollama pull qwen2.5-coder:1.5b`.

## Usage
```
python -m codemax                    # Groq, confirm mode
python -m codemax --provider ollama  # local model
python -m codemax --auto             # tools run without asking
```
In the REPL: `/auto`, `/confirm`, `/tools`, `/help`, `/exit`.
On start, CodeMax launches the MCP servers (needs Node/npx) and loads their tools automatically. Tests: `pytest`.

## Configuration
Copy `.env.example` to `.env`:
- `CODEMAX_PROVIDER`: `groq` (default) or `ollama`
- `GROQ_API_KEY`, `GROQ_MODEL` (default `openai/gpt-oss-120b`)
- `OLLAMA_MODEL`, `OLLAMA_BASE_URL` (default `http://localhost:11434`)
- `CONTEXT7_API_KEY` (optional, raises Context7 rate limits)

Run `python -m servers.rag_server.ingest` once before first use so the RAG server has an index.
Tool confirmation: confirm mode (default) asks before each file/shell action; `--auto` or `/auto` runs without asking.

## MCP servers
1. Filesystem (`@modelcontextprotocol/server-filesystem`)
2. Context7
3. Custom RAG server over the RAGAs docs (`servers/rag_server/`)

### Custom RAG server
Pipeline: RAGAs markdown docs -> heading-aware chunks -> `all-MiniLM-L6-v2` embeddings (local) -> persisted ChromaDB.
Query: top 20 by vector similarity, then reordered by a cross-encoder (`ms-marco-MiniLM-L-6-v2`) and the top k returned by the `rag_search(query, k)` tool.

```
python -m servers.rag_server.ingest      # run once (clones docs, builds servers/rag_server/chroma_db); reused afterwards
python -m servers.rag_server.evaluate    # vector vs. vector+rerank comparison for the report
```

## Project layout
See SPEC.md section 5.
