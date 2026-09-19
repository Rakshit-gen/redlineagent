import csv
import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select

from app.db import get_session
from app.models import AgentRun, Contract
from app.schemas import ContractCreate, ContractRead

router = APIRouter()


@router.get("/contracts/", response_model=list[ContractRead])
def list_contracts(session: Session = Depends(get_session)):
    return session.exec(select(Contract)).all()


@router.post("/contracts/", response_model=ContractRead)
def create_contract(payload: ContractCreate, session: Session = Depends(get_session)):
    contract = Contract(**payload.model_dump())
    session.add(contract)
    session.commit()
    session.refresh(contract)
    return contract


@router.get("/contracts/{contract_id}/", response_model=ContractRead)
def get_contract(contract_id: int, session: Session = Depends(get_session)):
    contract = session.get(Contract, contract_id)
    if contract is None:
        raise HTTPException(404, "Contract not found.")
    return contract


@router.get("/contracts/{contract_id}/report/")
def export_contract_report_csv(contract_id: int, session: Session = Depends(get_session)):
    contract = session.get(Contract, contract_id)
    if contract is None:
        raise HTTPException(404, "Contract not found.")

    run = session.exec(
        select(AgentRun).where(AgentRun.contract_id == contract_id).order_by(AgentRun.started_at.desc())
    ).first()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["topic", "severity", "clause_excerpt", "note", "suggested_language", "dismissed"])
    if run:
        for flag in run.flags:
            writer.writerow(
                [flag.topic, flag.severity, flag.clause_excerpt, flag.note, flag.suggested_language, flag.dismissed]
            )
    buffer.seek(0)
    filename = f"{contract.vendor_name.replace(' ', '_')}_redline_report.csv"
    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
