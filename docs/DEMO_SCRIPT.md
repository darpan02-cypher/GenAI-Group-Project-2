# Check-in demo script (Thu Oct 8)

Goal: show 2 of 3 MCP servers (filesystem + Context7) working inside the agent loop, then present
challenges and next steps. Total time: about 5 minutes.

## Pre-flight (do 15 minutes before)
- [ ] `source .venv/bin/activate && pytest` shows all tests passing
- [ ] `.env` has a working `GROQ_API_KEY` (test: `python -m codemax`, type `/tools`, `/exit`)
- [ ] Node is installed (`node -v`) and the internet works (Context7 and Groq are remote)
- [ ] Run the demo prompts once beforehand so `npx` has cached both servers (first run downloads them)
- [ ] Clean demo folder: `mkdir -p ~/codemax-demo && cd ~/codemax-demo`, then launch from there so MCP is scoped to it
      (`python -m codemax` with the repo's venv: `~/path/to/repo/.venv/bin/python -m codemax`)
- [ ] Terminal font large, dark theme, window wide (tool panels are 80+ columns)
- [ ] Backup: a screen recording of a successful run, in case the network fails

## Flow

### 1. Introduce (30 s)
"CodeMax is an autonomous CLI coding agent. Loop: reason, act, observe, repeat. It works with Groq
or a local Ollama model. Tools come from built-ins and from MCP servers loaded at startup."

Launch `python -m codemax`. Point at the startup lines:
`MCP connected: filesystem (14 tools)` and `MCP connected: context7 (2 tools)`.
Type `/tools` to show the dynamically loaded tools and which ones ask for confirmation.

### 2. Task A: confirm mode, Context7 + file write (2 min)
Mode: confirm (default).

> Use Context7 to find out what the Ragas faithfulness metric measures, then create notes.md with a 2-line summary.

What to point out as it runs:
- "Thinking..." spinner, then streamed text
- `context7__resolve-library-id` then `context7__query-docs` panels (the external MCP server)
- The yellow **Tool request** panel before the write: nothing is written until we press `y`
- Result panel, then the final summary

### 3. Task B: auto mode, filesystem MCP + shell (2 min)
Type `/auto` (note the yellow warning), then:

> List the files in this folder using the filesystem server, create fizzbuzz.py with a fizzbuzz(n) function and test_fizzbuzz.py with pytest tests, run the tests, and fix anything that fails.

Point out: `filesystem__*` tool calls, `run_shell` running pytest, the agent reading a failure and fixing it
(if it passes first time, say so: the loop only repeats when it needs to). Tools run without prompts in auto mode.

### 4. Challenges and next steps (1 min)
See below. Close with the roadmap.

## If something goes wrong
| Problem | What to do |
|---|---|
| `LLM call failed ... retrying` | Expected sometimes: Groq rejects malformed tool JSON, the loop retries automatically. Say so. |
| Agent loops or stalls | Ctrl+C returns to the prompt. Max-iteration guard stops it at 15 anyway. |
| Context7 slow or down | Skip to filesystem tasks, mention it is a remote service. Show the backup recording. |
| Groq rate limit | Wait 30 s or switch model: `GROQ_MODEL=<other>` in `.env`. |

## Challenges to present
1. **MCP SDK v2 renamed its API** (snake_case fields, `FastMCP` became `MCPServer`). We found it by testing against the real servers, not docs.
2. **The sync agent loop vs the async MCP SDK.** Solved with one background event loop thread.
3. **Models differ a lot in tool calling.** `openai/gpt-oss-120b` on Groq sometimes emits invalid tool-call JSON
   on long file contents. We added retries with a corrective nudge. The 1.5B local model (`qwen2.5-coder:1.5b`)
   writes tool calls as plain text instead of structured calls, so it cannot drive the loop at all.
4. **Models need the working directory.** MCP filesystem tools need absolute paths. Without it the model guessed paths and wasted calls. Fixed in the system prompt.
5. **Hardware limits** on one dev machine (disk, 8 GB RAM) restrict local model size.

## Next steps (after check-in)
- Custom RAG MCP server over the RAGAs docs: ingest once, persistent Chroma, cross-encoder reranking, `rag_search` tool (third server).
- Run the same coding task on 2+ LLMs (Groq models vs a larger local Ollama model) and record success, steps, time.
- RAG before/after reranking evaluation.
- CLI polish and branding, README, demo video, PDF report, architecture + state + sequence diagrams.
