from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models import LeaveRequest, LeaveType, ApprovalStatus

router = APIRouter(prefix="/api/leave", tags=["leave"])


class LeaveCreate(BaseModel):
    applicant: str
    department: str
    leave_type: LeaveType
    start_date: datetime
    end_date: datetime
    reason: str


class LeaveApprove(BaseModel):
    status: ApprovalStatus
    approver: str
    approval_comment: str = ""


@router.get("/")
def list_leaves(status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(LeaveRequest)
    if status:
        query = query.filter(LeaveRequest.status == status)
    return query.order_by(LeaveRequest.created_at.desc()).all()


@router.post("/")
def create_leave(req: LeaveCreate, db: Session = Depends(get_db)):
    leave = LeaveRequest(**req.model_dump())
    db.add(leave)
    db.commit()
    db.refresh(leave)
    return leave


@router.post("/{leave_id}/approve")
def approve_leave(leave_id: int, req: LeaveApprove, db: Session = Depends(get_db)):
    leave = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="请假申请不存在")
    leave.status = req.status
    leave.approver = req.approver
    leave.approval_comment = req.approval_comment
    db.commit()
    db.refresh(leave)
    return leave


@router.get("/{leave_id}")
def get_leave(leave_id: int, db: Session = Depends(get_db)):
    leave = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="请假申请不存在")
    return leave
