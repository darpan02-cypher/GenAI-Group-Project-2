# Project Plan: CLI Coding Assistant (Group Project 2)

**Team: 5** 
Himanshi Shrivas (A)
Amit Singh (B)
Calib Gilmore (C)
Kacey Eddia (D)

**Check-in:** Thu Oct 8 | **Final due:** Thu Oct 15, 11:59pm


## Goal
Autonomous CLI coding agent: agentic loop + LLM tool calling + MCP client connecting to 3 servers (filesystem, external resource, custom RAG) + provider abstraction (Ollama + 1 cloud) + streaming CLI with confirm/auto modes.

## Planned stack
- Python, LangChain (provider abstraction), MCP Python SDK
- MCP servers: `@modelcontextprotocol/server-filesystem`, Tavily or Context7, custom RAG server
- RAG: ChromaDB + sentence-transformers, docs of one library (e.g., LangChain). Advanced technique picked from NirDiamant/RAG_Techniques (e.g., reranking, query transformation, or contextual compression)
- CLI: `rich` / `prompt_toolkit`

## Roles (owner = primary, buddy = reviewer)

| Area | Owner | Buddy | Scope |
|---|---|---|---|
| Agent core | A | B | Agentic loop (reason, act, observe, repeat), stop conditions, max-iteration guard, provider abstraction (Ollama + cloud), config |
| CLI / UX | B | A | REPL, streaming, visible tool calls, status spinners, confirm vs auto-execute mode, branding |
| MCP client + servers | C | D | Dynamic tool loading from multiple servers, filesystem server, external server (Tavily/Context7), error handling |
| Custom RAG MCP server | D | C | Load docs, chunk, embed, store in Chroma (one-time ingest), query tool, advanced RAG technique |

**Shared (everyone):** diagrams, README, report, demo, LLM comparison, RAG evaluation.

## Working rules
- `main` is protected. Feature branches + PRs, 1 reviewer (buddy).
- Planning docs (this plan, architecture/state/sequence diagrams, specs) are committed **before** any implementation. Commit history must show this.
- Define interfaces up front so work runs in parallel: `LLMProvider.chat(messages, tools)`, `MCPClient.list_tools()/call_tool()`, `rag_search(query, k)` MCP tool.
- 15-min sync twice a week (suggest Mon + Wed) plus async chat. Blockers get posted same day.

## Week 1: Oct 1 – Oct 8 (target: check-in with 2+ MCP servers working)

**Thu Oct 1 – Fri Oct 2: Planning (all)**
- Pick assistant name, repo structure, tech stack, RAG library + technique
- Draft architecture/state diagram (A + B), sequence diagrams for 3 operations (C + D)
- Write specs/interfaces, README skeleton, `requirements.txt`
- Commit all planning docs. **No code before this is merged.**

**Sat Oct 3 – Mon Oct 5: Core build (parallel)**
- A: Basic agentic loop + Ollama provider + 1 cloud provider (Groq/OpenAI/Anthropic)
- B: REPL skeleton, streaming output, tool-call display panel, confirm/auto toggle
- C: MCP client, connect to filesystem server, load tools dynamically
- D: Doc ingestion pipeline (load, chunk, embed, Chroma), basic retrieval MCP server

**Tue Oct 6 – Wed Oct 7: Integrate**
- C adds external server (Tavily or Context7)
- A wires MCP tools into the loop; B hooks CLI into the loop
- D exposes RAG as MCP tool, connects through C's client
- End-to-end test: one task using filesystem + external server minimum (RAG ideally)

**Wed Oct 7 evening: Check-in prep (all)**
- Demo script, list of challenges + next steps, rehearse once

**Thu Oct 8: CHECK-IN**
- Show filesystem server + external server working (RAG too if ready, for the 2-of-3 requirement)
- Discuss challenges and next steps

## Week 2: Oct 9 – Oct 15 (target: submission)

**Fri Oct 9 – Sun Oct 11: Complete features**
- D: Implement/finish advanced RAG technique, run before/after retrieval comparison
- A: Harden loop (error recovery, retries, no stalls), test all providers
- B: Polish CLI (colors, status indicators, confirmation UX, branding/banner)
- C: Stabilize all 3 servers, test failure cases (server down, bad tool args)

**Mon Oct 12: Feature freeze + evaluation**
- Pick 2 non-trivial demo tasks (e.g., "add a feature + tests to a repo", "fix a bug using library docs")
- Run the **same coding task on 2+ LLMs** (e.g., Ollama local model vs cloud model), record: success, steps, time, quality
- D records RAG technique impact (examples + observations)

**Tue Oct 13: Deliverables (parallel)**
- A + B: Record demo video (2 tasks, all 3 MCP servers visibly invoked, tool calls on screen)
- C: Finalize README (setup, usage, env vars), `requirements.txt`, clean up/comment code
- D: Updated architecture diagram if anything changed (keep the original too)

**Wed Oct 14: Report**
- PDF report sections: system + design decisions (D), LLM comparison (A + C), RAG analysis (A), MCP + architecture changes (B), reflection (B)
- Everyone reviews the

