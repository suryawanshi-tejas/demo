# AI Career Copilot

![CI](https://github.com/YOUR_USERNAME/job-hunt-copilot/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11-blue)
![LangGraph](https://img.shields.io/badge/LangGraph-multi--agent-green)
![MCP](https://img.shields.io/badge/MCP-server-purple)

A multi-agent job search copilot: upload your resume, pull matching roles
from real job APIs, see your skill gap per role, generate a tailored resume +
cover letter, and track your application funnel — all grounded strictly in
your actual experience (no fabricated claims). One core (`src/`) exposed
three ways: a Streamlit dashboard, a FastAPI REST API, and an MCP server.

Inspired by enterprise-scale multi-agent orchestration patterns used in production AI systems, this project applies similar architectural principles to a personal career assistant.

## Why I Built This

Most job platforms rely heavily on keyword matching, making it difficult to identify roles that align with a candidate's actual experience and transferable skills.

I built AI Career Copilot to explore how modern AI engineering techniques—including LangGraph multi-agent workflows, semantic embeddings, retrieval-augmented reasoning, and Model Context Protocol (MCP)—can improve the entire application workflow.

Rather than being another chatbot demo, the goal was to build an end-to-end AI platform that helps candidates discover relevant opportunities, identify skill gaps, generate tailored application documents, and track their progress through a single unified system.

**[Live demo](#)** *(add your Streamlit Cloud URL here after deploying)*

## What it does

1. **Upload resume** (PDF/DOCX) → LLM structures it into a profile (titles,
   skills, experience bullets).
2. **Fetch jobs** via a LangGraph pipeline across five sources: **Adzuna**
   (UK/Ireland/Germany), **Arbeitnow** and **Remotive** (free, EU/remote),
   and **Greenhouse**/**Lever** (per-company public board APIs), plus manual
   URL paste for any job board — then dedupes.
3. **Score & rank** every job against your resume by **embedding cosine
   similarity** — not just title keyword matching, so it catches roles with
   different titles doing the same work.
4. **Skill gap analysis**: for any job, see matched vs. missing skills and a
   short roadmap to close the gap.
5. **Generate**: pick a job → tailored resume + cover letter, rendered to
   `.docx`, downloadable straight from the dashboard.
6. **Application tracker**: mark jobs saved/applied/interviewing/offer/
   rejected; see funnel counts, acceptance rate, and top companies applied to.
7. **Three interfaces, one core**: the Streamlit dashboard, a FastAPI REST
   API (`backend/`), and an **MCP server** (`mcp_server/`) that lets Claude
   Desktop or Claude Code call `search_jobs`, `generate_tailored_documents`,
   `get_skill_gap`, `track_application`, etc. directly as agent tools.

## What it deliberately does *not* do

No LinkedIn or Indeed scraping. Both prohibit automated scraping in their
ToS, and building around that isn't something I want in a repo I point
recruiters at. Every source here (Adzuna, Arbeitnow, Remotive, Greenhouse,
Lever) has a genuine public API intended for this use case.

## Architecture

```
                 ┌─────────────┐
   resume.pdf ──►│resume_parser│──► profile JSON (SQLite)
                 └─────────────┘
   Adzuna ─────┐
   Arbeitnow ──┤                    ┌───────────────────────────────────┐
   Remotive ───┼──► fetch_* nodes ─►│         graph.py (LangGraph)       │
   Greenhouse ─┤                    │ fetch → dedupe → score → store     │──► SQLite `jobs`
   Lever ──────┤                    └───────────────────────────────────┘
   manual URL ─┘                                    │
                                                      ▼
                                       matcher.py (embedding similarity)
                                                      │
                          ┌───────────────────────────┼───────────────────────────┐
                          ▼                            ▼                           ▼
                 app.py (Streamlit)          backend/main.py (FastAPI)   mcp_server/server.py (MCP)
                 dashboard, tracker,         REST API for the same       tools for Claude Desktop /
                 skill gap, Excel export     core logic                  Claude Code

                                    all three call the same src/ core:
                    skill_gap.py · generator.py · applications.py · cache.py (dual-key)
```

### Dual-key cache (`src/cache.py`)

Mirrors the TCS caching design: a `match_key` (hash of the exact profile +
job) for verbatim repeats, and a `shape_key` (title + company + first 40
words of the JD) so a near-duplicate posting scraped from a second board
still hits cache instead of triggering a fresh, costly generation call.
Used by both resume tailoring and skill-gap analysis.

## Quickstart

```bash
git clone https://github.com/YOUR_USERNAME/job-hunt-copilot.git
cd job-hunt-copilot
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Add ANTHROPIC_API_KEY (generation) and ADZUNA_APP_ID/ADZUNA_APP_KEY
# (free at https://developer.adzuna.com/). Arbeitnow/Remotive/Greenhouse/
# Lever need no key.

streamlit run app.py
```

### Running the FastAPI backend

```bash
uvicorn backend.main:app --reload --port 8000
# docs at http://localhost:8000/docs
```

### Running the MCP server

```bash
python mcp_server/server.py
```

Add it to Claude Desktop's `claude_desktop_config.json` (or Claude Code's
MCP config) to call it as agent tools:

```json
{
  "mcpServers": {
    "job-hunt-copilot": {
      "command": "python",
      "args": ["/absolute/path/to/job-hunt-copilot/mcp_server/server.py"]
    }
  }
}
```

Then you can ask Claude things like *"search for GenAI Engineer roles in
Germany and Ireland, then generate tailored docs for the top match"* and it
will call `search_jobs`, `list_top_jobs`, `generate_tailored_documents`, etc.

### Running everything with Docker

```bash
docker compose up --build
# Streamlit: http://localhost:8501
# FastAPI:   http://localhost:8000/docs
```

Both containers share a `data/` volume (SQLite DB + generated docs), so
resume uploads and fetched jobs are visible from either interface.

## Tests

```bash
pytest -v
```

All tests run offline (fake embeddings, isolated temp SQLite DB) — no API
keys or network calls required in CI.

## Legal note on job sourcing

This project only pulls from **Adzuna** and **Arbeitnow**, both of which
provide free, terms-of-service-compliant public APIs for exactly this use
case. It does not scrape LinkedIn, Indeed, or other boards that prohibit
automated scraping in their ToS — the manual-URL-paste feature is for you
to bring in a specific posting you found yourself.

## Roadmap

- ✅ V1 — resume upload, Adzuna + Arbeitnow, semantic matching, dashboard,
  tailored resume/cover letter generation, Excel export
- ✅ V2 (this version) — Remotive/Greenhouse/Lever sources, skill gap
  analyzer, application tracker + analytics, FastAPI backend, MCP server,
  Docker Compose
- 🔜 V3 — combine with [career-rag-assistant](../career-rag-assistant): expose
  the RAG career knowledge base as a tool the generation agent can call for
  richer, retrieval-grounded tailoring; pgvector instead of in-memory
  embedding comparison; auth for multi-user use

## Tech stack

LangGraph · LangChain · FastAPI · MCP · embedding-based semantic matching ·
SQLite · Streamlit · python-docx · Adzuna, Arbeitnow, Remotive, Greenhouse &
Lever APIs · Docker Compose · pytest · GitHub Actions
