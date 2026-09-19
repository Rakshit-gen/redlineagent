from app.engine import run_agent
from app.llm import MockLLMClient
from app.models import Contract, PolicyRule


def _make_rule(session, **overrides):
    defaults = dict(
        topic="auto_renewal",
        guidance="Auto-renewal without an opt-out window locks you in.",
        severity="high",
        risk_keywords="automatically renew,auto-renew",
        fallback_language="Renews only on mutual written consent.",
    )
    defaults.update(overrides)
    rule = PolicyRule(**defaults)
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return rule


def test_risky_clause_gets_flagged(session):
    _make_rule(session)
    contract = Contract(vendor_name="Acme", raw_text="This Agreement will automatically renew each year.")
    session.add(contract)
    session.commit()
    session.refresh(contract)

    run = run_agent(session, contract, llm=MockLLMClient())

    assert run.status == "completed"
    assert len(run.flags) == 1
    assert run.flags[0].topic == "auto_renewal"
    assert run.flags[0].severity == "high"


def test_clean_contract_gets_no_flags(session):
    _make_rule(session)
    contract = Contract(vendor_name="Acme", raw_text="This Agreement has a fixed one-year term.")
    session.add(contract)
    session.commit()
    session.refresh(contract)

    run = run_agent(session, contract, llm=MockLLMClient())

    assert run.status == "completed"
    assert run.flags == []


def test_every_topic_is_checked(session):
    _make_rule(session, topic="auto_renewal")
    _make_rule(
        session,
        topic="liability_cap",
        risk_keywords="unlimited liability",
        fallback_language="Liability capped at 12 months of fees.",
    )
    contract = Contract(vendor_name="Acme", raw_text="Vendor accepts unlimited liability for any claim.")
    session.add(contract)
    session.commit()
    session.refresh(contract)

    run = run_agent(session, contract, llm=MockLLMClient())

    searched_topics = {s.tool_args["topic"] for s in run.steps if s.tool_name == "search_clause"}
    assert searched_topics == {"auto_renewal", "liability_cap"}
    assert len(run.flags) == 1
    assert run.flags[0].topic == "liability_cap"


def test_every_step_is_recorded(session):
    _make_rule(session)
    contract = Contract(vendor_name="Acme", raw_text="This Agreement will automatically renew each year.")
    session.add(contract)
    session.commit()
    session.refresh(contract)

    run = run_agent(session, contract, llm=MockLLMClient())

    assert [s.step_number for s in run.steps] == list(range(1, len(run.steps) + 1))
    assert run.steps[-1].tool_name == "finish"


def test_analysis_with_no_policy_rules_yields_empty_run(session):
    contract = Contract(vendor_name="Acme", raw_text="Anything at all.")
    session.add(contract)
    session.commit()
    session.refresh(contract)

    run = run_agent(session, contract, llm=MockLLMClient())

    assert run.status == "completed"
    assert run.flags == []
    assert len(run.steps) == 1
    assert run.steps[0].tool_name == "finish"


def test_contract_status_becomes_reviewed(session):
    _make_rule(session)
    contract = Contract(vendor_name="Acme", raw_text="Fixed term, no auto-renewal here.")
    session.add(contract)
    session.commit()
    session.refresh(contract)

    run_agent(session, contract, llm=MockLLMClient())

    assert contract.status == "reviewed"
