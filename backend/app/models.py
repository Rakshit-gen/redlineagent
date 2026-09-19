from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, JSON
from sqlmodel import Field, Relationship, SQLModel


class PolicyRule(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    topic: str = Field(unique=True, index=True)
    guidance: str
    severity: str = "medium"
    risk_keywords: str
    fallback_language: str


class Contract(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    vendor_name: str
    raw_text: str
    status: str = "pending"
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AgentRun(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    contract_id: int = Field(foreign_key="contract.id")
    status: str = "running"
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    decided_at: Optional[datetime] = None

    steps: list["AgentStep"] = Relationship(back_populates="run")
    flags: list["Flag"] = Relationship(back_populates="run")


class AgentStep(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: int = Field(foreign_key="agentrun.id")
    step_number: int
    thought: str
    tool_name: str
    tool_args: dict = Field(default_factory=dict, sa_column=Column(JSON))
    observation: dict = Field(default_factory=dict, sa_column=Column(JSON))

    run: Optional[AgentRun] = Relationship(back_populates="steps")


class Flag(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: int = Field(foreign_key="agentrun.id")
    topic: str
    clause_excerpt: str
    severity: str
    note: str
    suggested_language: str
    dismissed: bool = False

    run: Optional[AgentRun] = Relationship(back_populates="flags")
