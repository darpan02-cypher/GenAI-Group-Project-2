# PLAN: CodeMax

Source of truth for scope is [SPEC.md](SPEC.md). This file covers order of work and deadlines.
Check-in: Thu Oct 8 (2 of 3 MCP servers demoed + challenges and next steps). Final: Thu Oct 15, 11:59pm.

## Tracks (owners to be confirmed by the team)
| Track | Scope |
|---|---|
| A: Agent core | Agentic loop, stop conditions, max-iteration guard, `LLMProvider` (Ollama + Groq), config |
| B: CLI / UX | REPL, streaming, tool-call display, spinners, confirm vs auto mode, branding |
| C: MCP client + servers | MCP client, filesystem server, Context7, dynamic tool loading, error handling |
| D: Custom RAG server | RAGAs docs ingest (once), Chroma, `rag_search`, reranking |
| Diagrams | State diagram + 3 sequence diagrams, original and updated architecture (teammate TBD) |

Everyone shares: README, report, demo, LLM comparison, RAG evaluation.

## Working rules
- Feature branches + PRs into `main`, one reviewer each.
- Planning docs are committed before any code. Commit history must show this.
- Interfaces in SPEC.md section 6 stay stable so tracks run in parallel.
- Small commits, one concern each. Code stays commented and explainable.

## Milestones
| Step | Target | What |
|---|---|---|
| 1. Plan docs | Oct 4 | SPEC.md, PLAN.md, README skeleton committed. ARCHITECTURE.md with diagrams from the diagram owner |
| 2. Scaffold + core | Oct 5 | Repo structure, requirements.txt, providers, minimal loop, basic streaming CLI with confirm/auto |
| 3. MCP client + 2 servers | Oct 7 | Filesystem + Context7 loaded dynamically and visible in the CLI. Check-in prep Oct 7 evening |
| Check-in | Oct 8 | Demo 2 of 3 servers, list challenges and next steps |
| 4. Custom RAG server | Oct 9-11 | Ingest once, persistent Chroma, reranking, wired into the agent |
| 5. Polish + deliverables | Oct 12-14 | Feature freeze Oct 12. LLM comparison, RAG before/after, demo video, README, PDF report |
| Submit | Oct 15 | Final checklist against rubric, submit before 11:59pm |

## Step 2 detail (my track, next)
1. Create the package skeleton and requirements.txt.
2. `providers/`: `LLMProvider` interface, Ollama and Groq implementations, selected by config.
3. `agent/`: loop (call LLM, run tool calls, feed results back, stop on final answer or max iterations).
4. `tools/`: read, write, edit, shell, search.
5. `cli/` (with B): minimal REPL with streaming, tool-call display, confirm/auto toggle.

## Rubric checklist (final)
Planning/Docs 10, Agentic Loop/Architecture 20, Tool Calling/CLI 20, MCP Integration 20, Custom RAG 20, Reflection + Demo 10, Participation 10, Check-in 10.

## Risks
- Check-in is Oct 8, so filesystem + Context7 come before RAG.
- Small local Ollama models may call tools poorly. Pick a tool-capable model early.
- Groq free-tier rate limits during long loops. Add retries and backoff.
