import csv
import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select

from app.db import get_session
from app.engine import run_agent
from app.models import AgentRun, Contract, Flag
from app.schemas import AgentRunRead, DismissFlag, FlagRead

router = APIRouter()


@router.post("/contracts/{contract_id}/analyze/", response_model=AgentRunRead)
def analyze_contract(contract_id: int, session: Session = Depends(get_session)):
    contract = session.get(Contract, contract_id)
    if contract is None:
        raise HTTPException(404, "Contract not found.")
    if contract.status == "reviewed":
        raise HTTPException(409, "Contract has already been reviewed.")
    return run_agent(session, contract)


@router.get("/runs/", response_model=list[AgentRunRead])
def list_runs(session: Session = Depends(get_session)):
    return session.exec(select(AgentRun)).all()


@router.get("/runs/export/")
def export_runs_csv(session: Session = Depends(get_session)):
    runs = session.exec(select(AgentRun)).all()
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["run_id", "contract_id", "status", "started_at", "decided_at", "flag_count"])
    for run in runs:
        writer.writerow([run.id, run.contract_id, run.status, run.started_at, run.decided_at, len(run.flags)])
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=agent_runs.csv"},
    )


@router.get("/runs/{run_id}/", response_model=AgentRunRead)
def get_run(run_id: int, session: Session = Depends(get_session)):
    run = session.get(AgentRun, run_id)
    if run is None:
        raise HTTPException(404, "Run not found.")
    return run


@router.post("/flags/{flag_id}/dismiss/", response_model=FlagRead)
def dismiss_flag(flag_id: int, payload: DismissFlag, session: Session = Depends(get_session)):
    flag = session.get(Flag, flag_id)
    if flag is None:
        raise HTTPException(404, "Flag not found.")
    flag.dismissed = payload.dismissed
    session.add(flag)
    session.commit()
    session.refresh(flag)
    return flag
