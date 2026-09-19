import re
from dataclasses import dataclass
from typing import Callable

from app.models import Contract, PolicyRule


@dataclass
class ToolResult:
    output: dict


@dataclass
class Tool:
    name: str
    func: Callable[..., ToolResult]


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def call(self, name: str, args: dict) -> ToolResult:
        return self._tools[name].func(**args)


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()]


def _find_clause(contract: Contract, policy_rule: PolicyRule) -> ToolResult:
    keywords = [k.strip().lower() for k in policy_rule.risk_keywords.split(",")]
    for sentence in _sentences(contract.raw_text):
        lowered = sentence.lower()
        if any(k in lowered for k in keywords):
            return ToolResult({"found": True, "excerpt": sentence})
    return ToolResult({"found": False, "excerpt": None})


def flag_risk() -> Tool:
    def _run(topic: str, excerpt: str, severity: str, note: str, suggested_language: str) -> ToolResult:
        return ToolResult(
            {
                "topic": topic,
                "excerpt": excerpt,
                "severity": severity,
                "note": note,
                "suggested_language": suggested_language,
            }
        )

    return Tool(name="flag_risk", func=_run)


def build_default_registry(contract: Contract, policy_rules_by_topic: dict[str, PolicyRule]) -> ToolRegistry:
    registry = ToolRegistry()

    def _search(topic: str) -> ToolResult:
        return _find_clause(contract, policy_rules_by_topic[topic])

    registry.register(Tool(name="search_clause", func=_search))
    registry.register(flag_risk())
    return registry
