from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models import ExpenseReport, ApprovalStatus

router = APIRouter(prefix="/api/expense", tags=["expense"])


class ExpenseCreate(BaseModel):
    applicant: str
    department: str
    category: str
    amount: float
    description: str


class ExpenseApprove(BaseModel):
    status: ApprovalStatus
    approver: str
    approval_comment: str = ""


@router.get("/")
def list_expenses(status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(ExpenseReport)
    if status:
        query = query.filter(ExpenseReport.status == status)
    return query.order_by(ExpenseReport.created_at.desc()).all()


@router.post("/")
def create_expense(req: ExpenseCreate, db: Session = Depends(get_db)):
    expense = ExpenseReport(**req.model_dump())
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


@router.post("/{expense_id}/approve")
def approve_expense(expense_id: int, req: ExpenseApprove, db: Session = Depends(get_db)):
    expense = db.query(ExpenseReport).filter(ExpenseReport.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="报销单不存在")
    expense.status = req.status
    expense.approver = req.approver
    expense.approval_comment = req.approval_comment
    db.commit()
    db.refresh(expense)
    return expense


@router.get("/{expense_id}")
def get_expense(expense_id: int, db: Session = Depends(get_db)):
    expense = db.query(ExpenseReport).filter(ExpenseReport.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="报销单不存在")
    return expense
