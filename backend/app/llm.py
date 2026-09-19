from dataclasses import dataclass
from typing import Optional, Protocol


@dataclass
class AgentAction:
    thought: str
    tool_name: Optional[str]
    tool_args: dict
    done: bool = False


class LLMClient(Protocol):
    def next_action(
        self,
        *,
        vendor_name: str,
        topics: list[str],
        policy_rules: dict[str, dict],
        history: list[dict],
    ) -> AgentAction: ...


class MockLLMClient:
    """Deterministic, rule-based planner: no network calls, no API key.

    Walks the policy playbook one topic at a time. For each topic it first
    searches the contract text for a matching clause, then — only if one was
    found — flags the risk using that policy rule's severity and fallback
    language. This keeps the loop fully auditable: every decision traces
    back to a concrete tool observation, never a black-box guess.
    """

    def next_action(
        self,
        *,
        vendor_name: str,
        topics: list[str],
        policy_rules: dict[str, dict],
        history: list[dict],
    ) -> AgentAction:
        searched = {h["tool_args"]["topic"] for h in history if h["tool_name"] == "search_clause"}
        flagged = {h["tool_args"]["topic"] for h in history if h["tool_name"] == "flag_risk"}

        if history:
            last = history[-1]
            if last["tool_name"] == "search_clause" and last["observation"]["found"]:
                topic = last["tool_args"]["topic"]
                if topic not in flagged:
                    rule = policy_rules[topic]
                    return AgentAction(
                        thought=f"Clause found for '{topic}'; it matches a policy red flag, so I'll flag it.",
                        tool_name="flag_risk",
                        tool_args={
                            "topic": topic,
                            "excerpt": last["observation"]["excerpt"],
                            "severity": rule["severity"],
                            "note": rule["guidance"],
                            "suggested_language": rule["fallback_language"],
                        },
                    )

        remaining = [t for t in topics if t not in searched]
        if remaining:
            topic = remaining[0]
            return AgentAction(
                thought=f"Checking the contract for a '{topic}' clause.",
                tool_name="search_clause",
                tool_args={"topic": topic},
            )

        return AgentAction(
            thought=f"All {len(topics)} playbook topics checked for {vendor_name}. Review complete.",
            tool_name=None,
            tool_args={},
            done=True,
        )
