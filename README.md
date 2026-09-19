# redlineagent

An agentic vendor-contract compliance reviewer. Paste in a vendor's contract
text and the agent checks it clause by clause against a policy playbook,
flags anything that violates your standard terms, and proposes fallback
language for each flag — a redline report a human reviews and can export.

## The problem

A small company without in-house legal signs dozens of vendor contracts a
year — SaaS subscriptions, payroll processors, logistics APIs — and almost
never reads them closely. Enterprise contract-review tools like Ironclad,
Spellbook, and LinkSquares solve this, but they're priced and scoped for
legal teams running high volumes through a CLM pipeline, not for a
five-person startup that just wants to know "does this auto-renew without
telling us, and is the liability cap reasonable."

`redlineagent` checks exactly the handful of clauses that matter most for a
non-lawyer: auto-renewal, liability caps, payment terms, data processing,
and unilateral termination. It doesn't replace a lawyer for anything
complex, but it catches the boilerplate traps before you sign.

## How the agent works

Each contract review runs through an observe → plan → act loop, persisted
step by step:

1. **search_clause** — for each policy playbook topic in turn, search the
   contract text for a matching clause.
2. **flag_risk** — if a clause was found, flag it using that topic's
   severity, guidance, and fallback language from the playbook.

The planner (`LLMClient`) is a protocol, not a hardcoded call. By default
it's `MockLLMClient` — deterministic, rule-based, no network calls, no API
key — so the project runs and its test suite passes with zero setup. Set
`OPENAI_API_KEY` and the engine switches to `OpenAIClient`, which drives the
same two tools via OpenAI's real tool-calling API instead of a fixed rule.
The loop, the tools, and the audit trail don't change — only the planner
does.

Every step and every flag is stored, not just the final report, so a human
can see exactly which sentence triggered which flag before deciding what to
do with it — dismiss a flag that doesn't apply, or use the suggested
fallback language in a redline back to the vendor. The agent never edits or
sends anything; it reads and proposes.

## Stack

- **Backend**: FastAPI + SQLModel, SQLite for local/demo use.
- **Frontend**: Next.js (App Router) + TypeScript + Tailwind.

## Running locally

```bash
# backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.seed
uvicorn app.main:app --reload

# frontend
cd frontend
npm install
npm run dev
```

Open the frontend, upload a contract (or use one of the seeded ones), click
"Analyze," and read the flagged clauses and agent trace. Set
`OPENAI_API_KEY` in the backend's environment to use a real model instead
of the deterministic mock planner.

## What's not built

No parsing of real contract file formats (PDF, DOCX) — contracts are
plain-text input, since the agent loop and clause matching are the point,
not document ingestion. No clause-level diffing against a prior contract
version. No e-signature or CLM integration — this produces a report for a
human to act on, it doesn't send anything back to the vendor.
