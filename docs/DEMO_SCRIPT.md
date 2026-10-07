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

## Token budget (read this: it decides whether the demo works)
Groq's free tier is limited per model: **8,000 tokens/minute and 200,000 tokens/day**. One agent turn costs
about 2,500+ tokens (tool schemas are re-sent every call), so a full task is roughly 10,000 to 30,000 tokens.
- Do NOT rehearse repeatedly on the demo day's key. Each model has its own daily pool, so rehearse on a
  different model (`GROQ_MODEL=openai/gpt-oss-20b`) and keep `openai/gpt-oss-120b` fresh for the demo.
- The daily limit resets on a rolling window (about 10 minutes of headroom returned after hitting it).
- A key with Groq Dev Tier, or a teammate's separate key, removes the problem.
- If the agent prints "Rate limit needs ~N min", stop and switch model; do not wait on stage.

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

> Using the filesystem server, list the files in this folder, then create greet.py that prints "Hello from CodeMax" and run it with python3.

Point out: the `filesystem__list_directory` call, the file write, `run_shell` running the script, and the agent
reading the output and finishing. Tools run without prompts in auto mode. This task is deliberately small to
stay within the Groq token limits.

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
