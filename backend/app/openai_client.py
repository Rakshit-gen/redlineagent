"""Optional real LLM-backed contract reviewer.

Not used unless OPENAI_API_KEY is set — the engine falls back to
MockLLMClient otherwise, so the project runs and tests fully offline.

Uses OpenAI's tool-calling API rather than free-text JSON parsing: the model
is given the two real tool schemas (search_clause, flag_risk) and either
picks one or replies with plain content to signal it's done. This keeps the
real planner's action space identical to what MockLLMClient can produce —
the engine can't tell them apart.
"""

from __future__ import annotations

import json
import os
import urllib.request

from .llm import AgentAction

SYSTEM_PROMPT = (
    "You are a vendor-contract compliance agent. You are given a vendor's contract "
    "text (implicitly, via the tools available to you), a policy playbook of topics "
    "to check, and a log of tool calls already made this run. Call search_clause to "
    "look for a clause on a topic you haven't checked yet. Only call flag_risk for a "
    "topic right after search_clause found a clause for it, using that policy rule's "
    "severity, guidance (as the note) and fallback_language (as suggested_language). "
    "Once every topic in the playbook has been checked, reply with plain text instead "
    "of a tool call to finish the review."
)


def _tool_schemas(topics: list[str]) -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": "search_clause",
                "description": "Search the contract for a clause matching a policy playbook topic.",
                "parameters": {
                    "type": "object",
                    "properties": {"topic": {"type": "string", "enum": topics}},
                    "required": ["topic"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "flag_risk",
                "description": "Flag a risky clause that a prior search_clause call found for a topic.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string", "enum": topics},
                        "excerpt": {"type": "string"},
                        "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                        "note": {"type": "string"},
                        "suggested_language": {"type": "string"},
                    },
                    "required": ["topic", "excerpt", "severity", "note", "suggested_language"],
                },
            },
        },
    ]


class OpenAIClient:
    """Real LLM-backed reviewer, driven via OpenAI tool calling. Requires OPENAI_API_KEY."""

    def __init__(self, model: str = "gpt-4o-mini", api_key: str | None = None):
        self.model = model
        self.api_key = api_key or os.environ["OPENAI_API_KEY"]

    def next_action(self, *, vendor_name, topics, policy_rules, history) -> AgentAction:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps({
                    "vendor_name": vendor_name,
                    "policy_rules": policy_rules,
                    "tool_call_history": history,
                })},
            ],
            "tools": _tool_schemas(topics),
            "tool_choice": "auto",
        }
        request = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            body = json.loads(response.read())

        message = body["choices"][0]["message"]
        tool_calls = message.get("tool_calls") or []
        if not tool_calls:
            return AgentAction(
                thought=message.get("content") or "Review complete.",
                tool_name=None,
                tool_args={},
                done=True,
            )

        call = tool_calls[0]["function"]
        return AgentAction(
            thought=message.get("content") or f"Calling {call['name']}.",
            tool_name=call["name"],
            tool_args=json.loads(call["arguments"]),
        )


def get_llm_client():
    """Real client if OPENAI_API_KEY is set, else the deterministic mock."""
    from .llm import MockLLMClient

    if os.environ.get("OPENAI_API_KEY"):
        return OpenAIClient()
    return MockLLMClient()
