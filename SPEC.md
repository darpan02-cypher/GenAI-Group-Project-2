# SPEC: CodeMax (CLI AI Coding Assistant)

Group Project 2. Check-in: Thu Oct 8. Final due: Thu Oct 15, 11:59pm. 120 pts.

## 1. What we are building
**CodeMax** is an autonomous CLI coding agent (not a chatbot). The user types a task in plain English. The agent reasons, calls tools to read/edit files and run commands, observes the results, and loops until the task is done.

## 2. Decisions (calibrated)
| Area | Decision |
|---|---|
| Product name | CodeMax |
| Language / framework | Python, LangChain, official MCP Python SDK |
| Providers | Ollama (local) + Groq (cloud), behind one abstraction |
| CLI libraries | `rich` + `prompt_toolkit` |
| MCP server 1 | Official filesystem server (`@modelcontextprotocol/server-filesystem`) |
| MCP server 2 | Context7 (external library-docs server) |
| MCP server 3 | Custom RAG server over the **RAGAs** docs |
| Vector DB / embeddings | ChromaDB (persisted on disk) + sentence-transformers (local) |
| Advanced RAG technique | **Reranking** (cross-encoder) from NirDiamant/RAG_Techniques |
| Repo layout | One Python package with subfolders (see section 5) |
| My role | A: Agent core + provider abstraction |
| Diagrams | Owned by another teammate. Not part of my work now. |

## 3. Required components
1. **Agentic loop**: reason, act, observe, iterate. Modular, with a stop condition and a max-iteration guard.
2. **Provider abstraction**: Ollama and Groq behind one interface (`LLMProvider.chat(messages, tools)`).
3. **Tool calling**: read, edit and write files, run shell commands, search the codebase. Two modes: confirm-before-execute and auto-execute. Every tool call is visible in the terminal.
4. **CLI**: terminal REPL, streaming responses, status indicators during tool execution, visually appealing.
5. **MCP client**: loads tools dynamically from the three servers above.
6. **Custom RAG MCP server**: load, chunk, embed, store in Chroma, query. Ingest runs once and later sessions reuse the persisted DB. Reranking is the advanced technique.

## 4. Deliverables
- GitHub repo: planning docs committed before any code, clean commented code, README with setup, requirements.txt.
- Video demo: 2 non-trivial autonomous tasks, all 3 MCP servers visibly invoked, tool calls and reasoning on screen.
- PDF report: system and design decisions, comparison of 2+ LLMs on the same coding task, RAG technique analysis, reflection, architecture diagram(s).
- Diagrams (other teammate): 1 state diagram, sequence diagrams for 3 distinct end-to-end operations.

## 5. Planned repo layout
```
codemax/
  agent/        # agentic loop, stop conditions
  providers/    # LLMProvider interface, Ollama, Groq
  cli/          # REPL, streaming, tool-call display, confirm/auto
  mcp_client/   # connects to servers, lists and calls tools
  tools/        # built-in file / shell / search tools
servers/
  rag_server/   # custom RAG MCP server (ingest, query, rerank)
docs/           # planning docs, diagrams
tests/
```

## 6. Interfaces (so teammates can work in parallel)
- `LLMProvider.chat(messages, tools)`: returns streamed text and/or tool calls.
- `MCPClient.list_tools()` / `MCPClient.call_tool(name, args)`.
- `rag_search(query, k)`: MCP tool exposed by the RAG server.

## 7. Out of scope (needs explicit approval)
Session persistence/resume, undo, image input, diff preview, any extra provider, tool or library beyond the above.

## 8. Execution plan
1. Plan docs: SPEC.md, ARCHITECTURE.md, PLAN.md, README skeleton. Commit before any code.
2. Scaffold + core: repo structure, requirements.txt, providers, minimal loop, basic streaming CLI with confirm/auto modes.
3. MCP client + 2 servers (filesystem, Context7). This is the Oct 8 check-in target.
4. Custom RAG MCP server (ingest once, persistent DB, reranking), wired into the agent.
5. Polish + deliverables: CLI branding, 2+ LLM comparison, RAG before/after evaluation, README, demo script, report inputs, rubric checklist.

## 9. Open items
- Team size: the master command says 4. The old plan draft said "5" but listed 4 names. Treated as 4 unless corrected.
- The old Project_Plan.md and architecture PNG are early drafts, not source of truth. I have not touched them.
- ARCHITECTURE.md and PLAN.md are still to be written. The architecture and diagram parts belong to the teammate who owns diagrams.
