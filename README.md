# redlineagent

Paste in a vendor contract and it checks the clauses a small company most often gets burned by: auto-renewal, liability caps, payment terms, data processing and termination. For each one it finds, it quotes the sentence, says why it matters and offers replacement wording you can send back to the vendor. A person reviews the result; the agent never edits or sends anything.

## Why

A company with no in-house lawyer signs dozens of vendor contracts a year (SaaS tools, payroll, logistics APIs) and rarely reads them closely. Ironclad, Spellbook and LinkSquares solve this for legal teams with a contract pipeline. A five-person startup just wants to know: does this auto-renew without telling us, and is the liability cap reasonable?

redlineagent covers that handful of checks. It will not replace a lawyer for anything complex, but it catches the common traps before you sign.

## How it works

You keep a **policy playbook**: one rule per topic, with risk keywords, a severity, guidance text and fallback language. Five rules are seeded:

| Topic | Severity |
|---|---|
| `auto_renewal` | high |
| `liability_cap` | high |
| `data_processing` | high |
| `payment_terms` | medium |
| `termination_for_convenience` | medium |

When you analyze a contract, the agent walks the playbook with two tools:

1. **`search_clause(topic)`** splits the contract into sentences and returns the first one containing any of that rule's keywords.
2. **`flag_risk(...)`** records a flag for that topic with the sentence, the rule's severity, its guidance as the note and its fallback language as the suggested wording.

Each step (the planner's thought, the tool, its input and output) is saved, and so is each flag. In the UI you can see exactly which sentence set off which flag, then dismiss the ones that do not apply.

The step budget grows with the playbook (two steps per topic plus one), so adding rules does not silently cut the review short.

### Two planners, one loop

The decision of what to call next comes from an `LLMClient` interface (`backend/app/llm.py`):

- **`MockLLMClient`** (default). Fixed order, no network, no key: search each topic, flag it if a clause was found, finish. The project runs and its tests pass offline.
- **`OpenAIClient`**. Used when `OPENAI_API_KEY` is set. It gives `gpt-4o-mini` the same two tools through OpenAI's tool calling, with the topic list as an enum, so the model can only choose actions the mock could also choose.

## Quickstart

Backend:

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.seed
uvicorn app.main:app --reload
```

Frontend, in another terminal:

```bash
cd frontend
cp env.example .env.local
npm install
npm run dev
```

Open http://localhost:3000, pick a seeded contract or paste your own text, click **Analyze** and read the flags and the trace.

## Configuration

| Variable | Where | Default | What it does |
|---|---|---|---|
| `OPENAI_API_KEY` | backend | unset | Switches to the OpenAI planner |
| `DATABASE_URL` | backend | `sqlite:///./redlineagent.db` | Any SQLAlchemy URL |
| `NEXT_PUBLIC_API_BASE` | frontend | `http://127.0.0.1:8000/api` | Backend URL |

## API

All under `/api`.

| Method | Path | What it does |
|---|---|---|
| `POST` | `/contracts/` | Add a contract (vendor name and raw text) |
| `GET` | `/contracts/`, `/contracts/{id}/` | List or read contracts |
| `POST` | `/contracts/{id}/analyze/` | Run the review, returns the run with steps and flags |
| `GET` | `/contracts/{id}/report/` | Flags for one contract as CSV |
| `POST` | `/flags/{id}/dismiss/` | Dismiss a flag |
| `GET` | `/runs/`, `/runs/{id}/` | Read runs |
| `GET` | `/runs/export/` | All runs as CSV |
| `GET`, `POST` | `/policy-rules/` | Read or add playbook rules |

## Layout

```
backend/app/engine.py         the review loop
backend/app/llm.py            planner interface and the rule-based mock
backend/app/openai_client.py  OpenAI planner with tool calling
backend/app/tools.py          search_clause and flag_risk
backend/app/seed.py           the five starter rules and sample contracts
backend/app/routers/          HTTP routes
backend/tests/                engine, API and planner selection tests
frontend/app/                 contract list, contract review, playbook editor
```

Tests: `cd backend && pytest`. CI runs them plus a frontend build.

## Limits

- Matching is by keyword. A clause is flagged because it mentions the topic, not because the agent decided the terms are bad. A fair liability cap gets flagged the same as an unfair one, which is what the dismiss button is for.
- Only the first matching sentence per topic is checked.
- Plain text only. No PDF or DOCX parsing.
- No comparison against an earlier version of the same contract.
- SQLite and no auth by default. Meant for local use.
