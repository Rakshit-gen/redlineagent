from datetime import datetime

from pydantic import BaseModel, Field


class PolicyRuleCreate(BaseModel):
    topic: str = Field(min_length=1)
    guidance: str = Field(min_length=1)
    severity: str = "medium"
    risk_keywords: str = Field(min_length=1)
    fallback_language: str = Field(min_length=1)


class PolicyRuleRead(PolicyRuleCreate):
    id: int


class ContractCreate(BaseModel):
    vendor_name: str = Field(min_length=1)
    raw_text: str = Field(min_length=1)


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
