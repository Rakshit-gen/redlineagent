from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models import Contract
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
