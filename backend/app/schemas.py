from datetime import datetime

from pydantic import BaseModel


class PolicyRuleCreate(BaseModel):
    topic: str
    guidance: str
    severity: str = "medium"
    risk_keywords: str
    fallback_language: str


class PolicyRuleRead(PolicyRuleCreate):
    id: int


class ContractCreate(BaseModel):
    vendor_name: str
    raw_text: str


class ContractRead(BaseModel):
    id: int
    vendor_name: str
    raw_text: str
    status: str
    uploaded_at: datetime


class AgentStepRead(BaseModel):
    id: int
    step_number: int
    thought: str
    tool_name: str
    tool_args: dict
    observation: dict


class FlagRead(BaseModel):
    id: int
    topic: str
    clause_excerpt: str
    severity: str
    note: str
    suggested_language: str
    dismissed: bool


class AgentRunRead(BaseModel):
    id: int
    contract_id: int
    status: str
    started_at: datetime
    decided_at: datetime | None
    steps: list[AgentStepRead] = []
    flags: list[FlagRead] = []


class DismissFlag(BaseModel):
    dismissed: bool = True
