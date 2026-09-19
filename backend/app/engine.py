from datetime import datetime, timezone

from sqlmodel import Session, select

from app.llm import LLMClient
from app.models import AgentRun, AgentStep, Contract, Flag, PolicyRule
from app.openai_client import get_llm_client
from app.tools import build_default_registry

MAX_STEPS = 12


def run_agent(session: Session, contract: Contract, llm: LLMClient | None = None) -> AgentRun:
    llm = llm or get_llm_client()
    rules = session.exec(select(PolicyRule)).all()
    policy_rules_by_topic = {r.topic: r for r in rules}
    topics = list(policy_rules_by_topic.keys())

    registry = build_default_registry(contract, policy_rules_by_topic)

    run = AgentRun(contract_id=contract.id)
    session.add(run)
    session.commit()
    session.refresh(run)

    history: list[dict] = []
    for step_number in range(1, MAX_STEPS + 1):
        rule_dicts = {
            t: {"severity": r.severity, "guidance": r.guidance, "fallback_language": r.fallback_language}
            for t, r in policy_rules_by_topic.items()
        }
        action = llm.next_action(
            vendor_name=contract.vendor_name,
            topics=topics,
            policy_rules=rule_dicts,
            history=history,
        )

        if action.done or action.tool_name is None:
            step = AgentStep(
                run_id=run.id,
                step_number=step_number,
                thought=action.thought,
                tool_name="finish",
                tool_args={},
                observation={},
            )
            session.add(step)
            break

        result = registry.call(action.tool_name, action.tool_args)
        step = AgentStep(
            run_id=run.id,
            step_number=step_number,
            thought=action.thought,
            tool_name=action.tool_name,
            tool_args=action.tool_args,
            observation=result.output,
        )
        session.add(step)

        if action.tool_name == "flag_risk":
            flag = Flag(
                run_id=run.id,
                topic=result.output["topic"],
                clause_excerpt=result.output["excerpt"],
                severity=result.output["severity"],
                note=result.output["note"],
                suggested_language=result.output["suggested_language"],
            )
            session.add(flag)

        history.append({"tool_name": action.tool_name, "tool_args": action.tool_args, "observation": result.output})

    run.status = "completed"
    run.decided_at = datetime.now(timezone.utc)
    contract.status = "reviewed"
    session.add(run)
    session.add(contract)
    session.commit()
    session.refresh(run)
    return run
