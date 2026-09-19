from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models import PolicyRule
from app.schemas import PolicyRuleCreate, PolicyRuleRead

router = APIRouter()


@router.get("/policy-rules/", response_model=list[PolicyRuleRead])
def list_policy_rules(session: Session = Depends(get_session)):
    return session.exec(select(PolicyRule)).all()


@router.post("/policy-rules/", response_model=PolicyRuleRead)
def create_policy_rule(payload: PolicyRuleCreate, session: Session = Depends(get_session)):
    existing = session.exec(select(PolicyRule).where(PolicyRule.topic == payload.topic)).first()
    if existing:
        raise HTTPException(409, f"A policy rule for topic '{payload.topic}' already exists.")
    rule = PolicyRule(**payload.model_dump())
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return rule
